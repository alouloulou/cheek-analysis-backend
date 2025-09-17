import express from 'express';
import { google } from 'googleapis';
import { JWT } from 'google-auth-library';
import { createClient } from '@supabase/supabase-js';

const app = express();
app.use(express.json({ type: '*/*' }));

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SERVICE_ROLE_KEY = process.env.SERVICE_ROLE_KEY!;
const GOOGLE_CREDENTIALS_JSON = process.env.GOOGLE_CREDENTIALS_JSON!;
const RTDN_VERIFICATION_TOKEN = process.env.RTDN_VERIFICATION_TOKEN!;

const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

function ok(res: express.Response) { return res.status(204).end(); }
function log(...args: any[]) { console.log('[RTDN]', ...args); }
function warn(...args: any[]) { console.warn('[RTDN]', ...args); }
function error(...args: any[]) { console.error('[RTDN]', ...args); }

app.post('/webhooks/google-play-rtdn', async (req, res) => {
  try {
    const tokenH = req.header('x-goog-channel-token')
      || req.header('X-Goog-Verification-Token')
      || (req.query.token as string | undefined);
    if (RTDN_VERIFICATION_TOKEN && tokenH !== RTDN_VERIFICATION_TOKEN) {
      warn('Token mismatch');
      return ok(res);
    }

    const message = req.body?.message;
    if (!message?.data) {
      log('No data in message');
      return ok(res);
    }

    const decoded = JSON.parse(Buffer.from(message.data, 'base64').toString('utf8'));
    const pkg = decoded.packageName;
    const sub = decoded.subscriptionNotification;
    const productId = sub?.subscriptionId;
    const purchaseToken = sub?.purchaseToken;
    const notifType = sub?.notificationType;

    log('Incoming RTDN', { pkg, productId, notifType, purchaseToken });

    if (!pkg || !productId || !purchaseToken) {
      warn('Missing pkg/productId/token; skipping');
      return ok(res);
    }

    const creds = JSON.parse(GOOGLE_CREDENTIALS_JSON);
    if (creds.private_key?.includes('\\n')) creds.private_key = creds.private_key.replace(/\\n/g, '\n');

    const auth = new JWT({
      email: creds.client_email,
      key: creds.private_key,
      scopes: ['https://www.googleapis.com/auth/androidpublisher'],
    });
    const androidpublisher = google.androidpublisher({ version: 'v3', auth });

    const resp = await androidpublisher.purchases.subscriptions.get({
      packageName: pkg,
      subscriptionId: productId,
      token: purchaseToken,
    });
    const data = resp.data;

    const expiryMs = data.expiryTimeMillis ? Number(data.expiryTimeMillis) : 0;
    const nowMs = Date.now();
    const isActive = expiryMs > nowMs;
    const endIso = expiryMs ? new Date(expiryMs).toISOString() : null;
    const cancellationReason = (data as any)?.cancelReason ?? (data as any)?.cancellationReason;

    const { data: profile, error: pErr } = await supabase
      .from('profiles')
      .select('id')
      .eq('last_purchase_token', purchaseToken)
      .maybeSingle();

    if (pErr) { error('profiles read error:', pErr.message); return ok(res); }
    if (!profile) { warn('No profile for token; skipping upsert'); return ok(res); }

    const status = isActive ? 'active' : 'expired';
    const update: Record<string, any> = {
      id: profile.id,
      subscription_status: status,
      subscription_type: productId.includes('year') ? 'yearly' : 'monthly',
      subscription_end_date: endIso,
      updated_at: new Date().toISOString(),
      last_package_name: pkg,
      last_product_id: productId,
      last_purchase_token: purchaseToken,
    };
    if (cancellationReason !== undefined) update.subscription_cancellation_reason = String(cancellationReason);

    const { error: uErr } = await supabase.from('profiles').upsert(update);
    if (uErr) error('profiles upsert error:', uErr.message);
    else log('profiles updated', { id: profile.id, status, endIso, cancellationReason });

    return ok(res);
  } catch (e: any) {
    error('handler error:', e?.message ?? String(e));
    return ok(res);
  }
});

app.get('/healthz', (_, res) => res.send('ok'));

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`RTDN webhook listening on :${port}`);
});
