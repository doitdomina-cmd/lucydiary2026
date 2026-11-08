/*
 * 정산 앱 「웹툰 투고 메일」 발송 서버 (Firebase Cloud Functions)
 *  - uploadPdf : 작품별 투고용 PDF를 서버 저장소에 올림 (한 번만)
 *  - sendMail  : 네이버 메일 계정으로 투고 메일 발송 (PDF 자동 첨부)
 * 비밀번호는 코드에 넣지 않고 Firebase 비밀 저장소(secrets)에 둠:
 *   NAVER_USER (네이버 아이디, @naver.com 앞부분) · NAVER_PASS (네이버 애플리케이션 비밀번호) · MAIL_KEY (앱과 서버가 나누는 비밀 열쇠)
 */
const { onRequest } = require('firebase-functions/v2/https');
const { defineSecret } = require('firebase-functions/params');
const admin = require('firebase-admin');
const nodemailer = require('nodemailer');

admin.initializeApp();
const NAVER_USER = defineSecret('NAVER_USER');
const NAVER_PASS = defineSecret('NAVER_PASS');
const MAIL_KEY = defineSecret('MAIL_KEY');

const OPTS = { region: 'asia-northeast3', cors: true, secrets: [NAVER_USER, NAVER_PASS, MAIL_KEY], memory: '512MiB', timeoutSeconds: 120, maxInstances: 3 };
const pdfPath = id => `submission-pdf/${String(id).replace(/[^\w-]/g, '_')}.pdf`;
const okKey = req => { const k = String(req.get('x-api-key') || ''); const m = MAIL_KEY.value(); return !!m && k.length === m.length && require('crypto').timingSafeEqual(Buffer.from(k), Buffer.from(m)); };
const validMail = s => /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(String(s || ''));

// PDF 올리기: PUT/POST ?workId=작품id  (본문 = PDF 파일 그대로)
exports.uploadPdf = onRequest({ ...OPTS, memory: '1GiB' }, async (req, res) => {
  if (req.method === 'OPTIONS') return res.status(204).send('');
  if (!okKey(req)) return res.status(401).json({ ok: false, error: '열쇠가 맞지 않아요.' });
  const workId = String(req.query.workId || ''); if (!workId) return res.status(400).json({ ok: false, error: '작품 정보가 없어요.' });
  const buf = req.rawBody; if (!buf || !buf.length) return res.status(400).json({ ok: false, error: '파일이 비어 있어요.' });
  if (buf.slice(0, 5).toString() !== '%PDF-') return res.status(400).json({ ok: false, error: 'PDF 파일이 아니에요.' });
  if (buf.length > 25 * 1024 * 1024) return res.status(413).json({ ok: false, error: 'PDF가 너무 커요. (25MB 이하)' });
  const name = String(req.query.name || 'attachment.pdf').slice(0, 120);
  await admin.storage().bucket().file(pdfPath(workId)).save(buf, { contentType: 'application/pdf', metadata: { metadata: { name, size: String(buf.length) } } });
  res.json({ ok: true, name, size: buf.length });
});

// PDF 정보 (올려 둔 게 있는지)
exports.pdfInfo = onRequest(OPTS, async (req, res) => {
  if (req.method === 'OPTIONS') return res.status(204).send('');
  if (!okKey(req)) return res.status(401).json({ ok: false, error: '열쇠가 맞지 않아요.' });
  const f = admin.storage().bucket().file(pdfPath(String(req.query.workId || '')));
  const [exists] = await f.exists(); if (!exists) return res.json({ ok: true, exists: false });
  const [m] = await f.getMetadata();
  res.json({ ok: true, exists: true, name: (m.metadata && m.metadata.name) || 'attachment.pdf', size: Number(m.size) });
});

// 메일 보내기: JSON { workId, to, subject, html, attachName }
exports.sendMail = onRequest(OPTS, async (req, res) => {
  if (req.method === 'OPTIONS') return res.status(204).send('');
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'POST만 돼요.' });
  if (!okKey(req)) return res.status(401).json({ ok: false, error: '열쇠가 맞지 않아요.' });
  const { workId, to, subject, html, attachName } = req.body || {};
  if (!validMail(to)) return res.status(400).json({ ok: false, error: '받는 사람 메일 주소가 올바르지 않아요.' });
  if (!subject || !String(subject).trim()) return res.status(400).json({ ok: false, error: '메일 제목이 비어 있어요.' });
  if (!html || !String(html).replace(/<[^>]*>/g, '').trim()) return res.status(400).json({ ok: false, error: '메일 본문이 비어 있어요.' });
  const attachments = [];
  if (workId) {
    const f = admin.storage().bucket().file(pdfPath(workId));
    const [exists] = await f.exists();
    if (!exists) return res.status(400).json({ ok: false, error: '이 작품에 올려 둔 PDF가 없어요.' });
    const [buf] = await f.download();
    attachments.push({ filename: String(attachName || 'attachment.pdf').replace(/[\\/:*?"<>|]/g, '_'), content: buf, contentType: 'application/pdf' });
  }
  const user = NAVER_USER.value().replace(/@naver\.com$/i, '');
  const transporter = nodemailer.createTransport({ host: 'smtp.naver.com', port: 465, secure: true, auth: { user, pass: NAVER_PASS.value() } });
  try {
    const info = await transporter.sendMail({
      from: `"${String(req.body.fromName || user).replace(/["\r\n]/g, '')}" <${user}@naver.com>`,
      to: String(to).trim(), subject: String(subject), html: String(html),
      text: String(html).replace(/<br\s*\/?>/gi, '\n').replace(/<\/(p|div|li)>/gi, '\n').replace(/<[^>]*>/g, ''),
      attachments
    });
    res.json({ ok: true, id: info.messageId, accepted: info.accepted });
  } catch (e) {
    console.error('send fail', e && e.message);
    res.status(502).json({ ok: false, error: '네이버 메일 서버에서 보내지 못했어요: ' + ((e && e.responseCode) ? e.responseCode + ' ' : '') + ((e && e.message) || '').slice(0, 160) });
  }
});
