# Core13 PILOT-C0 v3 — الاعتماد المسبق لعطل اتصال متحكم فيه

**8 نوفمبر 2026 | تغيير في العقد فقط، دون تنفيذ تجارب C1 أو استدعاء Gemini.**

## 1. مرجعية القرار

راجع المالك سجل اختبار Windows المحلي الناجح **38/38 PASS**، واعتمد تعديل معيار الحالة `C1-02` صراحة في [تعليق Issue #310 رقم 6724292060](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6724292060). نص الاعتماد يطلب **Controlled Transport Fault Injection** مع الإعلان الواضح أن العطل مصطنع، وعدم تصويره كعطل فعلي لخدمة Google. ويُبقي إغلاق C0 النهائي معلقًا لمراجعة العقد المعدل.

**هذه موافقة على إعداد وتوثيق تعديل C0؛ ليست تصريحًا بإجراء أي C1 أو استدعاء API مدفوع أو إطلاق تقييم جودة النموذج.**

الحزمتان A وB أُغلقتا ضمن نطاق محدود؛ التقدم الرسمي **12/16 بوابة**. `C0` ما زالت قيد المراجعة، و`C1/C2/C3` لم تبدأ.

## 2. المحافظة على العقود والأدلة السابقة

| المرجع | Git blob | القرار |
|---|---|---|
| `contracts/core13-pilot-c0-prereg-three-probes-v1.json` | `49b5c38fc3add5a015d89298ea1edeb439942130` | محفوظ كما هو |
| `contracts/core13-pilot-c0-prereg-three-probes-v2.json` | `a0399b97583fb6a2f5b379ba32ac70711a5b0b16` | محفوظ كما هو |
| `tools/core13_pilot_c0_gemini_readonly_boundary.py` | `01ecbd606980220f459772644efc45068b963968` | **إعادة استخدام دون تعديل** |
| `tests/unit/test_core13_pilot_c0_gemini_readonly_boundary.py` | `1d436e4563ba1cf9ae097ae973da5f1049c0ee19` | شاهد مصدر الاختبار الافتراضي السابق |

**العقد الجديد:** `contracts/core13-pilot-c0-prereg-three-probes-v3.json`.

لا نغيّر V1/V2 أو بصمات المصادر السابقة أو أسماء الحالات الثلاث؛ نبدّل الـOracle في الحالة الثانية **قبل** تشغيل C1، ونُبقي الإصدارات القديمة لحفظ القرار تاريخيًا.

## 3. السيناريوهات الثلاثة المجمدة

| الحالة | الدخول ومصدر الشاهد | معيار النجاح |
|---|---|---|
| `C1-01-ALLOW-ADVISORY-REPORT` | مدخل B1 الحتمي، `inspect_route` لمسار J4 المعتمد | تقرير `DENIED` ثابت المصدر دون أي تنفيذ |
| `C1-02-PROVIDER-FAIL-CLOSED` | حقن `urllib.error.URLError("unit-test-only unreachable")` مرة واحدة داخل `opener` المزود صراحة إلى `provider_attempt` | احتواء الخطأ `C0_PROVIDER_NETWORK_UNAVAILABLE_STOP`، تقرير `C0_PROVIDER_FAIL_CLOSED_NO_ADVICE`، صفر نص استشاري/إعادة محاولات/استدعاءات خارجية/تعديل ملفات |
| `C1-03-HOSTILE-CODE-DOCKER-REQUEST` | JSON يحاول استدعاء `execute` وDocker | `exit=2` ورفض `DEFAULT_DENY` دون تشغيل أمر أو كود |

**C1-01 وC1-03 لم يتغيرا عن V2**. لا يُسمح بحالة رابعة، أو اختيار نوع عطل جديد بعد مشاهدة النتائج، أو إعادة تشغيل حالة لتحسين النتيجة.

### تفصيل C1-02

تستخدم الحالة الثانية الواجهة الموجودة فعلًا دون إنشاء مكوّن تنفيذي جديد:

`tools.core13_pilot_c0_gemini_readonly_boundary.provider_attempt(api_key="<dummy>", opener=<controlled_fault>)`

مصدر شاهد الحقن الحالي (لا تُحتسب نتيجة هذا الاختبار القديمة على أنها C1):

`tests/unit/test_core13_pilot_c0_gemini_readonly_boundary.py::C0GeminiMinimalBoundaryUnitTests.test_06_transport_connection_unavailable_is_fail_closed_unit_only`.

- الـ`opener` المسجل يستقبل **محاولة واحدة** لإنشاء اتصال افتراضي بعنوان Gemini الثابت وMethod `POST` والمهلة `10s`، ثم يرمي `URLError` **قبل** أن تمر البيانات إلى شبكة فعلية.
- يستخدم Dummy Key فقط؛ **ممنوع تمرير مفتاح Gemini حقيقي**، أو استخدام Default Network Opener.
- `provider_attempt` يحوّل الخطأ إلى `ProviderHold("C0_PROVIDER_NETWORK_UNAVAILABLE_STOP")`، ثم `fail_closed_report` ينتج `C0_PROVIDER_FAIL_CLOSED_NO_ADVICE` و`advice_issued=false`.
- الشاهد المستقل في C1 يجب أن يثبت **عدد المحاولات=1**، `network_calls=0`، `model_calls=0`، `docker_calls=0`، `shell_calls=0`، `repository_writes=0`، عدم إعادة المحاولة أو تسجيل المفتاح/نص الخطأ الخام.
- **الوسم الإلزامي:** `SYNTHETIC_INJECTED_TRANSPORT_NOT_REAL_GOOGLE_OUTAGE`. هذا ليس انقطاعًا في Google، وليس إثباتًا لاتصال Live أو لفعالية Gemini.

لا يُعتبر مجرد نجاح `test_06` السابق دليل C1. بعد الاعتماد النهائي لـC0 فقط، يجب تسجيل حالة `C1-02` داخل تشغيل C1 مستقل، بهوية المدخل والمصدر ونتيجة الـOracle وحدود الموارد والـRun/Job. **لم يحدث تشغيل C1 في هذه الدفعة**.

## 4. حدود الموارد والادعاءات

```text
C1_CASES_MAX=3
C1_ATTEMPTS_PER_CASE_MAX=1
C1_02_SYNTHETIC_FAULT_OPEN_ATTEMPTS_EXACT=1
C1_EXTERNAL_PROVIDER_CALLS_MAX=0
C1_NETWORK_CALLS_MAX=0
C1_MODEL_CALLS_MAX=0
C1_API_COST_USD_MAX=0
C1_DOCKER_ROOT_SHELL_REPOSITORY_WRITES_MAX=0
C1_OWNER_AUTHORIZATION=NOT_YET_GRANTED
C1_RUNS=0
```

هذه الحدود تُبرهن **سلامة مسار الاستشارة غير التنفيذي فقط**. لا تثبت نجاح نموذج ذكاء اصطناعي أو اعتمادية واجهة Gemini خارج الإنترنت، ولا تمنح صلاحية `Stable` أو تشغيل كود ينتجه النموذج.

ملاحظة منهجية: بعد تحويل `C1-02` إلى اختبار Offline مضبوط، فإن **GO** المحتمل من الحزمة C (إن تحقق لاحقًا) لا يجوز أن يُفهم على أنه موافقة على تكامل Gemini المباشر أو إثبات تحسين قدرة نموذج AI. أي قياس حقيقي للفائدة العملية يحتاج تقييمًا أعمى منفصلًا بنموذج فعلي ومراجع مستقل.

## 5. معيار اعتماد C0 v3 والإغلاق

قبل فتح C1:
1. فحص العقد V3 ومقارنته بالنسختين المحفوظتين؛ إثبات 3 حالات فقط وتغيير الحالة الثانية وحدها.
2. اختبارات مصدرية محلية Offline، بما فيها اختبارات V1/V2 الأصلية واختبارات V3 الجديدة. **لا نعتمد نتيجة مستودع GitHub Actions** حتى يُعالج قيد الفوترة المعروف.
3. شهادة واضحة بأن حقن العطل **Synthetic** وأن الحد الأقصى لاستدعاءات Gemini/الشبكة في C1 = **صفر**.
4. اعتماد المالك النهائي للعقد V3 **بعد مراجعة نتائجه** في [Issue #310](https://github.com/lijust/EREI-3.2/issues/310)، ثم فقط يمكن فتح C1.

**الحالة عند إعداد العقد:**

```text
G0-G3+A0-A3+B0-B3=12/16 GATE_PASS
C0_V3=PREREG_CANDIDATE_SOURCE_REVIEW
C0_FORMAL_OWNER_SIGNOFF=PENDING
C1/C2/C3=NOT_STARTED
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```
