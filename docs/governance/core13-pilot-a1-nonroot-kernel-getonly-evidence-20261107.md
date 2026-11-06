# Core13 PILOT-A / A1 — Nonroot Kernel GET-only Proxy Negative Verification

**7 نوفمبر 2026 | حزمة A فقط | قرار A1: PRE_REVIEW / NOT_FORMALLY_CLOSED.**

## 1. ما الذي تنفذه A1 بالضبط؟

قبل أي تشغيل Root أو الاتصال بـDocker الحقيقي، يختبر هذا الجزء **سلوك Linux Kernel** مع Unix `AF_UNIX/SOCK_SEQPACKET` حقيقي و`SO_PEERCRED`، وسياسة قراءة مقيدة بثوابت مصدر A0. كل الاستجابات `STATIC_OFFLINE_TEST_BYTES_ONLY`، وليست بيانات Docker.

المكون: `tools/core13_pilot_a1_nonroot_unix_getonly_probe.py`.  
المصدر الملزم: `tools/core13_pilot_a0_readonly_docker_policy.py` Git blob `393140049b2a23ed8981e175b78df0bbb8702b94`، وعقد A0 Git blob `5b9af0c999afa636c735d7ac49ae5696a36f69bd`. تغير أحدهما يوقف التجربة ويستلزم إعادة مراجعة.

**المسموح به:** `GET /containers/json?all=1`، أو `GET /containers/<reviewed_cid>/json` حيث الـCID يمر كقيمة ثابتة مراجعَة في fixture غير صادرة من عميل غير موثوق.

**المرفوض:** جميع طلبات CREATE / DELETE / START / HEAD / PUT / تغيير GET Query أو Path / Header Injection / CID غير مصرح / استقبال SCM_RIGHTS FD / تجاوز 256 byte / Response أكبر من 65536 byte / Socket Symlink / Socket world-writable / اختلاف PID أو UID أو GID وفق `SO_PEERCRED` / Timeout.

## 2. فاصل أمان مهم يجب عدم تضخيمه

الاختبار يشغّل **Process child منفصلة فعلًا** وبـPID مختلف من خلال `fork()`، لكنه يستخدم **نفس UID/GID** للعملية الأصلية (لا نستطيع إسقاط صلاحيات مستخدم آخر في اختبار Nonroot عام). حالات اختلاف UID/GID هنا تغيّر **القيمة المتوقعة لدى المراقب** وتقارنها بهوية kernel الصحيحة؛ إنها اختبارات لصحة *قانون المقارنة*، وليست أدلة على عزل حسابات `runner` و`daemon` الحقيقيين.

اختبارات فصل المستخدمين الفعلية توجد في [F5B1J Run #42300277663](https://github.com/lijust/EREI-3.2/actions/runs/42300277663)، لكنها تخص **Proxy اصطناعي سابق**، ولا تعادل نجاح GET حقيقي في الحزمة A. لا يُسمح بترقية هذه النتائج إلى `A2` أو `Independent Settlement`.

## 3. تصميم الاختبارات وتقسيمها

| المجموعة | دليل السلوك المطلوب | نطاق النتيجة |
|---|---|---|
| Source gate | مراجعة Git Blob/عقد A0 وعدم السماح بتبديلهما | Source drift = DENY |
| Kernel Peer | PID حقيقي من `fork` وقيم UID/GID من `SO_PEERCRED`، رفض تطابق كاذب | Kernel comparison local |
| Allowed GET | `[]` للـInventory وJSON ثابت لـCID مراجع | Fixture only |
| Forbidden API | POST CREATE / DELETE / START / HEAD / query / CID غير مراجع | Deny قبل أي Backend |
| IPC / FD | `SCM_RIGHTS` يتم استلامه ثم إغلاقه ورفض الطلب؛ `MSG_TRUNC` رفضه | No FD widening |
| Filesystem | رفض Socket mode=0666 وsymlink بنفس الاسم المتوقع | Local filesystem |
| Availability | رفض عدم إرسال بيانات خلال مهلة قصيرة ورفض reply >64KiB | Fail-closed |
| CLI | Source-only preflight؛ لا Root ولا Docker ولا اعتمادات جديدة | HOLD |

**يجب أن يكون الاستدلال في تقارير CI واضحًا:** اختبار Kernel الحقيقي + Backend اصطناعي = `A1_NONROOT_NEGATIVE_SCOPED_PASS` بعد مراجعة الأدلة، **وليس** `A2_REAL_DOCKER_PASS`.

## 4. معيار إغلاق A1 الصارم

**المتطلبات جميعها إلزامية لإعلان `A1_GATED_PASS`:**
1. المصدر والـManifest والتبعيات ثابتة وتطابق SHA، وشفرة اختبارات Unix فعلية؛ لا Source-Grep وحده.
2. جميع اختبارات A1 وفحوص الحوكمة A0 ناجحة ضمن تشغيل CI واحد، مع رابط Run/Job وDecoded Logs.
3. تجارب الرفض تشاهد عن طريق Kernel socket فعلي: PID mismatch، SCM_RIGHTS، Packet truncation، Permission/Symlink، POST/DELETE/START وClient Timeout.
4. توثيق صريح بأن `UID/GID mismatch` محاكاة **للقيمة المتوقعة** وليس Process بUID مختلف؛ الدليل الحقيقي لتفريق الحسابات من F5B1J، وA2 يتحقق مرة أخرى من حساب Verifier الفعلي.
5. صفر Docker calls / صفر Root calls / صفر Model Code / Zero resource leaks في نطاق التجربة، مع قائمة المخاطر وحدود الاستنتاج.
6. قرار مالك موثق في Issue [#308](https://github.com/lijust/EREI-3.2/issues/308) مع اعتماد حوكمة `G3` من [#307](https://github.com/lijust/EREI-3.2/issues/307). لا تعتمد رسالة في ChatGPT وحدها باعتبارها شهادة GitHub.

**عند فشل شرط:** `A1_BLOCKED` وتُصرف جولة الإصلاح في حدود إجمالي دورتين للحزمة A. لا تُفتح F5B1L ولا تبدأ A2 تلقائيًا.

## 5. A2 وما بعده

A2 فقط تختبر **Root-owned GET-only Proxy نحو daemon ثانوي حقيقي** بعد نجاح A0/A1 وموافقة مالك خاصة. لا CREATE/START/DELETE في A. لا يُسمح بافتراض Terminal Settlement من استجابة Inventory فارغة. تبقى `stable_ready=false`، `AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE`.

## 6. حالة التنفيذ الأولية

```text
A1_SOURCE_PIN_AND_NONROOT_KERNEL_NEGATIVE=CI_PENDING
A1_ACTUAL_DISTINCT_UID_VERIFIER_TEST=NOT_EXECUTED_IN_THIS_PHASE
A1_REAL_DOCKER_GET=NOT_EXECUTED
G3_AUTHENTICATED_OWNER_SIGNOFF=NOT_RECORDED
A1_FORMAL_GATE_PASS=false
A2_OWNER_MANUAL_REAL_DOCKER=NOT_EXECUTED
A_CLOSED_PASS=false
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_ESTABLISHED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
stable_ready=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```
