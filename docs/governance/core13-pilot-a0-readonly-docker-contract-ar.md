# Core13 PILOT-A / A0 — عقد تنفيذ قراءة Docker الحقيقي فقط

**7 نوفمبر 2026 | الإصدار A0.1 | المرحلة: A0_DESIGN_PROPOSED (لم تُغلق).**  
المرجع: [عقد Pilot الإلزامي #307](https://github.com/lijust/EREI-3.2/issues/307)، [حزمة A #308](https://github.com/lijust/EREI-3.2/issues/308)، [التخطيط السابق F5B1K #305](https://github.com/lijust/EREI-3.2/issues/305).

## 0. قرار نطاق الحزمة: «قراءة فقط» وليس تجربة CREATE أخرى

**الهدف الوحيد:** تأكيد قدرة مراقب محمي بهوية Linux مختلفة عن Controller على الحصول على **بيانات حقيقية** من Docker Daemon **ثانوي ومعزول وقابل للحذف**، عبر وسيط محمي GET-only، مع إثبات منع أي طلب تعديل. لا يُستخدم Docker الافتراضي للمضيف، ولا يُرسل طلب CREATE أو START أو DELETE في حزمة A. لا يسمح PASS في A بترقية `EMITTED_UNKNOWN` إلى terminal أو بتدوير Generation غير محسومة.

**حد الصلاحية الحالي:** مراجعة تصميم/اختبارات Nonroot. عبارة «ابدأ» في المحادثة تُعد توجيهًا لبدء تنفيذ المنهجية، **لكن ليست شهادة اعتماد Github مستقلة**؛ يبقى `G3` بانتظار توقيع موثق في Issue #307 قبل إعلان A ACTIVE أو إجراء Owner-Manual Root. الكود والعقد لا يعدلان حالة G3 بصمت.

## 1. قيد الخلفية الذي يجب ألا يضيع

- [F5B1F #42202611269](https://github.com/lijust/EREI-3.2/actions/runs/42202611269): عملية CREATE ثابتة + INSPECT + DELETE على daemon ثانوي **بلا START**، ودليل `RETURNED_CLAIM` غير محسوم.
- [F5B1J #42300277663](https://github.com/lijust/EREI-3.2/actions/runs/42300277663): **242/242 PASS** واختبار Linux UID فعلي مع Proxy *اصطناعي* يرد `[]` ثم CID، وحفظ إيصال HMAC محلي Root. **لم يحصل على Docker حقيقي**.
- لا يوجد إثبات أن الحالتين في مسار واحد متكامل؛ لذلك تُختبر القراءة الحقيقية فقط دون زيادة صلاحيات.

## 2. نموذج التهديد وملكية الصلاحيات

| المكوّن | الصلاحيات الوحيدة في A | ما يُمنع |
|---|---|---|
| Controller — `runner` | طلب ملاحظة مراجعة ثابتة من واجهة Pilot مستقبلاً | فتح Docker socket أو قراءة مفتاح Verifier أو التحكم بـProxy أو تشغيل كود |
| Worker — `nobody` | لا يحتاج الوصول إلى Docker في A | كل Unix Docker Socket وكل مفاتيح الأدلة |
| Verifier — `daemon` (UID/GID مختلفة فعليًا عن `runner` و`nobody` وفق kernel) | إرسال GET محدود عبر Root-owned Proxy، قراءة مفتاح محمي محدود | مباشرة Docker Socket، إرسال CREATE/DELETE/START، إعادة تسمية مشروع أو إصدار تسوية |
| Root Proxy | الوصول الحصري **في fixture** إلى socket daemon ثانوي، قبول GET فقط بعد `SO_PEERCRED` | نقل HTTP عام، قبول method/path مرسل غير مراجَع، الوصول إلى host default |
| Secondary dockerd | تشغيل معزول بمسار بيانات وتنفيذ وSocket مؤقتة تحت `/run` | Host Docker daemon، أي container CREATE داخل A، TCP listeners |
| Evidence Store | إقرار محلي محدود بالقراءة، مربوط بالـBoot/PID/StartTicks/Nonce | التظاهر بأن HMAC المملوك Root إثبات مستقل عنه أو أنه append-only durable |

**شروط الحسابات قبل أي اختبار Root:** وجود الحسابات الثلاثة على Runner، وكونها Nonroot، واختلاف UID وGID فعليًا. إذا لم يوجد حساب `daemon` أو تطابقت الهوية مع `runner`/`nobody` يُرفض A2 دون إنشاء حسابات على الجهاز أو اختيار بديل صامت. لا يجوز استخدام نفس حساب `nobody` كـWorker وVerifier لأن ذلك يضع مفتاح المراقب تحت قدرة العامل.

التهديدات التي **يجب** اختبارها: UID/PID/GID مزوّر، socket قديم/مختلف، daemon PID reused، Boot ID غير مطابق، CID خارجي أو غير مراجع، query/path expansion، HTTP method تبديل، SCM_RIGHTS/FD inheritance، استدعاء host `/var/run/docker.sock`، التفاف عبر Controller/Worker، أخطاء مهلة/response truncation، اختفاء daemon منتصف GET، عدم إزالة ملفات fixture.

## 3. بروتوكول GET فقط (مغلق Default Deny)

يُقبل حصريًا:
1. `GET /containers/json?all=1` بدون Headers أو query إضافية من الطرف العميل؛ الاستجابة JSON bounded.
2. `GET /containers/{reviewed_cid}/json` حيث `reviewed_cid` بصمة CID ست عشرية من 64 خانة ومن **inventory فعلية للمصدر الثانوي أو WAL مراجعة**، وليست قيمة يحددها Controller اعتباطًا.

**كل ما عدا ذلك DENY**: `POST`, `DELETE`, `PATCH`, `PUT`, `HEAD`, `CONNECT`, `OPTIONS`, `GET /info`, `GET /version`, `GET /events`, `GET /containers/json`, query إضافية، URI مسلسلة/مشفرة، proxy catch-all، IPv4/IPv6 أو host socket. لا يتيح A التعامل مع حاوية جديدة؛ المتوقع أن تكون inventory *فارغة* ويُثبت الحصول على `[]` من daemon الحقيقي.

**تعريف «قراءة حقيقية»**: يجب أن يثبت Run Owner Manual تشغيل daemon الثانوي وصحة Kernel peer identity وsocket الخاص به، وقبول GET عبر Proxy المقيد وتسجيل Response حقيقي، مع إثبات رفض Controller والطرق الممنوعة؛ **الاستجابة الاصطناعية لا تكفي**.

## 4. خطة التنفيذ المعتمدة للحزمة A

| Gate | الحد الدقيق للنجاح | الاستبعاد الصريح |
|---|---|---|
| **A0** | هذا التهديد والعقد JSON متطابقان بالـSHA بين المستودعين، بوابة Policy offline تُحظر كل توسعة غير مصرح بها، مراجعة Source Pin/Root Bootstrap وCleanup مع أدلة CI + اعتماد مالك العقد | وثيقة فقط بلا Tests أو توقيع غير موثق |
| **A1** | Nonroot CI يثبت رفض UID/PID الخاطئ وطرق POST/DELETE/START وCID غير مطابق، ومفاتيح/Socket/FD افتراضية، وحالات timeout/overlength، دون Docker حقيقي أو sudo | Stub أو Source-Grep وحده لا يكفي عند إثبات سلوك OS |
| **A2** | Owner-only dispatch **بعد** A0/A1، daemon ثانوي حقيقي، GET-only عبر Root Proxy، Kernel identities، Host baseline unchanged، عدم CREATE/START/DELETE، cleanup=0 | PR/PUSH root، إثبات Mock فقط، أو Host docker modified |
| **A3** | أدلة SHA/Run/Job/logs، Negative witnesses، حدود الثقة، علامة no-container-left، Audit بشري وقرار `A_SCOPED_READ_ONLY_PASS` أو `CLOSED_NO_GO/BLOCKED` | ترقية مباشرة إلى Stable أو Independent Terminal Settlement |

## 5. تقسيم العمل بلا Overengineering

**المطلوب الجديد فقط:** `A0 Contract+offline validator`، `A1 kernel/Unix fake negative tests`، `A2 manually gated real-secondary-daemon GET-only proxy`، `A3 final evidence report`. نعيد استخدام `F5B1E/F5B1F` لتجهيز daemon وتشخيص baseline بدون تكرار مولدات Docker أو root wrappers؛ ونقتبس تحكم `F5B1J` في OS principals/Proxy من غير أن نخفي Source Pin للتبعيات. **لا نعدل F5 WAL، ولا ننشئ مسار CREATE جديدًا.**

يُمنع تعطيل قيود Source/Owner لحل CI. في حالة FAIL: محاولة إصلاح السبب ضمن **دورتين جذريتين فقط**، ثم A تُغلق NO_GO/BLOCKED مع سبب واضح؛ لا تُفتح F5B1L، ولا ترجع الحزمة B إلى التشغيل إن A فشلت.

## 6. فصل النتائج المطلوب

```text
A0_DESIGN_STATUS=PROPOSED_PENDING_G3_AND_CI_EVIDENCE
A1_OFFLINE_NEGATIVE=NOT_ESTABLISHED
A2_REAL_DOCKER_GET=NOT_EXECUTED
A3_PACKAGE_CLOSURE=NOT_STARTED
ROOT_HMAC_INDEPENDENT_FROM_ROOT=false
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_ESTABLISHED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
stable_ready=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```

هذه الوثيقة والعقد يجمّدان **ما يجب إثباته** فقط؛ لا تزعم إثبات وصول Docker الحقيقي حتى يُنجَز A2 لاحقًا.
