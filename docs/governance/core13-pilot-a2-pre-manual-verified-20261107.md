# Core13 PILOT-A2 — حالة المرشح الجاهز للاختبار اليدوي (2026-11-07)

## أدلة GitHub الفعلية

- App Draft PR [#314](https://github.com/lijust/EREI-3.2/pull/314)، Framework Draft PR [#174](https://github.com/lijust/EREI-Engineering-Framework/pull/174).
- [GitHub Actions #42372593592](https://github.com/lijust/EREI-3.2/actions/runs/42372593592)، Job **128403607704 = SUCCESS**.
- Decoded CI logs: **23 A2 offline source/negative tests** + **29 A1 Linux Unix/FDS** + **30 A0 policy** + **21 Governance** = **103/103 PASS**.
- Owner-manual real dockerd Job **128403648572 = SKIPPED** — **لا دليل بعد على A2 Real Docker GET**.
- فرع التنفيذ: `core13/pilot-a2-owner-manual-readonly-secondary-dockerd-20261107`.
- Source Git blob `tools/core13_pilot_a2_owner_real_dockerd_getonly_hold.py`: `0b220cb7aed71183ee6be1a98cfd112de46665ff`.

## المراجع المثبتة في الشيفرة

- `daemon.py` helper Git blob: `a609dce0a9fb6d362a3ddfec65fd7f6fde5188bc`.
- `b1b` fixed Unix Docker transport blob: `ba1f81bc70c45ff31042f1355ee99bbc291a2aa4`.
- `b1e` secondary real daemon init blob: `a24dbcde512adf75e2292da7530665f992662535`.
- `b1j` real OS principal child blob: `0d7cd8d69113ef1a08af9757e62b5286c623371b`.
- `A0` source: `393140049b2a23ed8981e175b78df0bbb8702b94`.
- `A0` contract: `5b9af0c999afa636c735d7ac49ae5696a36f69bd`.
- سابقًا F5B1J real root Linux/synthetic proxy (owner manual) [#42300277663](https://github.com/lijust/EREI-3.2/actions/runs/42300277663)؛ **غير بديل عن A2**.

## ما جرى تجهيزه في A2 ولم يتم تشغيله Root

- Root-only manual `workflow_dispatch` مع **اختيارين صريحين**: إقرار مراجعة الحوكمة G3، وإذن قراءة Docker الحقيقي فقط.
- تشغيل daemon ثانوي حصري `/run/core13-j504e2a-*` بالوظائف التي سبق مراجعتها، مع private socket `0600`.
- Proxy root-owned `0660` إلى Verifier `daemon` فقط مع `SO_PEERCRED` الدقيق، والتأكد من اختلاف الحسابات الحقيقية `runner`, `nobody`, `daemon`.
- عدد **4 طلبات inventory GET صريحة ومحددة** في المسار المراد اختباره: GET ابتدائي، GETين عبر Proxy، GET نهائي. قد يقوم helper daemon أيضًا بقراءة `/info` لأغراض الجاهزية والتحقق؛ لذلك **لا يُقال** إن العدد الكلي لكل طلبات Docker API =4.
- طلب POST اصطناعي إلى Proxy **يُرفض محليًا قبل الوصول إلى Docker**. صفر CREATE/START/DELETE مطلوبة أو مسموحة.
- تحقق انطباق Host DockerRootDir وقائمة Container IDs قبل/بعد؛ مصدر `docker ps --all --quiet --no-trunc` للقراءة فقط.
- HMAC محلي Root-provisioned مرتبط بالـNonce وVerifier UID وهوية daemon PID/BootID/StartTicks. **Root قادر على انتحال توقيع المراقب؛ ليس استقلالًا نهائيًا**.
- تأكيد غياب جذر `/run/` المؤقت بعد انتهاء العملية (أو FAIL)، وعدم ترقية F5 terminal/Stable أو صلاحية النموذج.

## حدود إغلاق الحزمة

| المسار | الحالة الدقيقة |
|---|---|
| Governance G3 | **NOT_RECORDED** كاعتماد مستقل في سجل الحزمة |
| A0 design CI | PASS_PRE_REVIEW (ليس formal Gate closure) |
| A1 actual nonroot kernel negatives | PASS_PRE_REVIEW (ليس formal Gate closure) |
| A2 source-only negative CI | **103/103 PASS** |
| A2 real Docker root manually | **SKIPPED / NOT_EXECUTED** |
| A3 complete owner acceptance packet | NOT_STARTED |
| Package A formally CLOSED_PASS | **FALSE** |
| Formal 16-gate closure | **0/16** |
| Independent L3 / Stable / AI acceptance | **NOT_ESTABLISHED / false / BLOCK_AI_ACCEPTANCE** |

**مهم:** لا يُنفذ صاحب المشروع Root job قبل مراجعة G3 وتوقيع سجل الحوكمة؛ لا نرسل طلب تشغيل Root آليًا. بمجرد التشغيل اليدوي، يجب قراءة سجل الـJob ثم اتخاذ `A2_GATED_PASS` أو `A2_NO_GO` وفق الأدلة، بلا مرحلة جديدة.
