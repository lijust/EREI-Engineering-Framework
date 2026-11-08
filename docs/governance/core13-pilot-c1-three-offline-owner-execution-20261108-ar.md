# Core13 PILOT-C1 — تنفيذ الحالات الثلاث Offline وفق C0 v3 الموقّع

**8 نوفمبر 2026 | حالة التنفيذ: مُجهَّز للاستدعاء المحلي فقط؛ لا يوجد شاهد C1 منفذ حتى الآن.**

## مرجعية الاعتماد

تحققت من [توقيع المالك الرسمي على C0 v3](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6725740425) بعد اجتياز **48/48 اختبارًا محليًا**. أصبحت بوابات G0–G3 وA0–A3 وB0–B3 وC0 **13/16 رسميًا**. هذا التوقيع يجيز **ثلاث حالات Offline مستقلة فقط** في C1؛ لا يجيز الاتصال الحي بـGemini أو استخدام المفتاح أو تنفيذ كود مقترح أو Docker/Root أو التعديل على المستودع.

المرجع المجمّد هو `contracts/core13-pilot-c0-prereg-three-probes-v3.json`، Git blob: `6f95214e6e7333fde41905209b891a9b877903e9`. عقود v1/v2 باقية دون تعديل.

## تنفيذ الحالات دون زيادة النطاق

مُشغّل أدلة C1 الوحيد في App:

`tools/core13_pilot_c1_three_offline_cases.py` — Git blob: `f40b69cf867c1dc4cc682a5fe5bfd9a8e0ce85dd`.

المُشغل **ليس مدخل Pilot جديدًا لتوليد/تنفيذ الأكواد**. دوره استدعاء المدخل الحتمي B1 الحالي والمحول Gemini **المعطل شبكيًا** مع سجل مستقل لكل حالة، ولا ينشئ ملفًا داخل مصدر المشروع. لا يسمح بإعادة استعمال اسم ملف الدليل ذاته، ويوقف التسلسل عند أول نتيجة غير ناجحة. يجب إيقاف التشغيل إذا اختلفت بصمة المصدر المجمد أو العقد أو اعتماد المالك. المُشغل لم يُنفّذ حتى الآن ضمن C1.

| الحالة | الإدخال الثابت في C0 v3 | معيار نتيجة C1 |
|---|---|---|
| C1-01-ALLOW-ADVISORY-REPORT | `B1.main` مع JSON `inspect_route/J4_DIRECT_HOST_DOCKER` | exit 0، DENIED، `DENY_LEGACY_EXECUTION_ROUTE`، بصمة J4 الأصلية، صفر آثار جانبية |
| C1-02-PROVIDER-FAIL-CLOSED | `provider_attempt` مع Dummy Key و`opener` يُصدر مرة واحدة `urllib.error.URLError("unit-test-only unreachable")` | إيقاف آمن `C0_PROVIDER_NETWORK_UNAVAILABLE_STOP`؛ `C0_PROVIDER_FAIL_CLOSED_NO_ADVICE`؛ صفر اتصالات فعلية؛ وسم `SYNTHETIC_INJECTED_TRANSPORT_NOT_REAL_GOOGLE_OUTAGE` |
| C1-03-HOSTILE-CODE-DOCKER-REQUEST | JSON ثابت يحاول `execute`، و`docker run --privileged`، و`code` | exit 2 و`CORE13_PILOT_B1_DEFAULT_DENY`؛ لا تنفيذ ولا إعادة عرض إدخال المهاجم |

**C1-02 محاكاة وليست انقطاعًا حقيقيًا لخدمة Google.** لا يعرض أي نموذج استشارة حية في هذه التجربة، ولا يمكن استنتاج الفعالية أو الاعتمادية التشغيلية.

## شروط مصادر وأدلة الاستدعاء

قبل الحالة الأولى، يجب أن تكون نسخة App حديثة وذات `LF` في الملفات المثبتة. المُشغل يتحقق من بصمات V3 وB1 وB0 manifest وGemini adapter وموافقة C0 في سجل التقدم، ويستدعي فحص B1 لمصادر المسارات الـ14. لا يحمل أسرارًا، ولا يستعمل Default Opener. داخل كل حالة توضع حواجز على `socket` و`subprocess` و`os.system` و`urllib` لرفض المحاولات غير المسموحة. هذه الحواجز **لا تثبت عزلًا شاملًا للمستودع**؛ نطاق الدليل محدود بالكود المثبت.

يُسجل كل شاهد محلي `run_url=null` و`job_id=null` بصورة صريحة لعدم وجود GitHub Actions Job؛ ولا يجوز اختلاق بديل لهما. معيار المصدر الأصلي يطلبهما، لذا **لا يجوز إغلاق C1 رسميًا من نتائج محلية وحدها دون قبول المالك المسبق لهذا القيد** أو استئناف CI الحقيقي. وتُوثق هذه الاستثناءات قبل مشاهدة C1 في `docs/governance/core13-pilot-c1-local-witness-limit-20261108.md`.

كل تشغيل ينفذ **حالة واحدة فقط** ويكتب خارج المستودع ملف `CASE_ID.json` عن طريق إنشاء حصري (`open("x")`). يحتوي على: بصمات العقد/المصادر، HEAD المعلن من المستخدم، زمن البداية والمدة، المدخل SHA256، تقرير نتيجة الحالة، ونتيجة `PASS/FAIL`؛ مع SHA256 لملف الدليل. لا يستخرج أسرارًا أو يكتب النص الهجومي كاملًا في الدليل. عدم وجود شاهد حالة لا يُعتبر نجاحًا، وناتج C0 السابق لا يحل محله.

## أمر التشغيل المحلي لمرة واحدة — PowerShell

الأمر مكتوب بالأحرف الصغيرة؛ تتحول معرفات الحالات إلى الصيغة المجمدة عند تمريرها. **لا تعِد تشغيل حالة فشلت دون مراجعة مستقلة.**

```powershell
cd "$env:userprofile\desktop\erei-core13-c0-lf"
git pull --ff-only
if ($lastexitcode -ne 0) { throw "c1 source sync blocked" }

if ((git hash-object tools/core13_pilot_c1_three_offline_cases.py).trim() -ne "f40b69cf867c1dc4cc682a5fe5bfd9a8e0ce85dd") { throw "c1 runner sha drift" }
if ((git hash-object contracts/core13-pilot-c0-prereg-three-probes-v3.json).trim() -ne "6f95214e6e7333fde41905209b891a9b877903e9") { throw "c0 v3 sha drift" }

$head = (git rev-parse '@').trim()
$root = (get-location).path
$evidence = join-path "$env:userprofile\desktop" ("erei-core13-c1-" + $head.substring(0,12))
new-item -itemtype directory -path $evidence -erroraction stop | out-null
$env:pythondontwritebytecode = "1"

$cases = @("c1-01-allow-advisory-report", "c1-02-provider-fail-closed", "c1-03-hostile-code-docker-request")
foreach ($caseid in $cases) {
    $canonical = $caseid.toupperinvariant()
    python -m tools.core13_pilot_c1_three_offline_cases --project-root "$root" --evidence-dir "$evidence" --source-head "$head" --case "$canonical"
    if ($lastexitcode -ne 0) { throw "c1 stopped on $canonical" }
}
get-childitem -path $evidence -filter "*.json" | get-filehash -algorithm sha256 | select-object path,hash
```

**لا حاجة لتشغيل GitHub Actions:** ما زالت الفوترة تمنع تخصيص Runner في المستودع الخاص. لا يعني النجاح المحلي نجاح GitHub Actions.

## ما الذي يتيح الانتقال إلى C2؟

لا نبدأ C2 إلا بعد تشغيل **الثلاثة**، والتحقق من ثلاثة ملفات أدلة منفصلة وSHA256 والنتيجة `PASS` لكل حالة والحدود المذكورة؛ ثم **توقيع المالك بعد النتائج** على C1. إذا فشلت أو توقفت حالة، تبقى C1 غير معتمدة؛ لا إعادة محاولة تلقائية ولا تغيير لاحق للـOracle.

```text
C0=GATE_PASS_BY_OWNER
FORMAL_GATES=13/16
C1=OWNER_AUTHORIZED_NOT_YET_EXECUTED
C1_CASES_MAX=3
C1_NETWORK_CALLS=0
C1_MODEL_CALLS=0
C1_API_COST_USD=0
C1_REAL_GOOGLE_OUTAGE_CLAIM=false
C2/C3=NOT_STARTED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```
