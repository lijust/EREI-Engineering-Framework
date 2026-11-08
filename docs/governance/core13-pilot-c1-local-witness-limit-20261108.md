# Core13 C1 — استثناء موثق ومسبق لوسيط أدلة التشغيل المحلي

**8 نوفمبر 2026 | قبل تشغيل أي حالة C1 | لا تُغيّر مدخلات أو أحكام C0 v3.**

## لماذا وُثّق ذلك؟

العقد المُعتمد `contracts/core13-pilot-c0-prereg-three-probes-v3.json` يحتفظ من النسخة الأصلية بمتطلبات أدلة تشمل `run_url` و`job_id` و`decoded_log_witness`. تشغيل GitHub-hosted Actions على App Private غير ممكن حاليًا؛ رسالة GitHub الموثقة تنص على **failed account payments or spending limit**، والوظائف فشلت قبل تخصيص Runner. لا يجوز وصف تشغيل محلي بأنه GitHub Actions Job.

المالك وقع [إغلاق C0 واعتماد 3 حالات Offline فقط](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6725740425)، لكن **لم يسجل بعد استبدال وسيط أدلة GH بإثبات محلي**. لذلك يلزم توثيق اختيار الوسيط **قبل مشاهدة أي نتيجة C1**، مع الاحتفاظ بالعقد المجمد كما هو. هذا ليس تغييرًا لمعيار PASS/FAIL، أو إضافة حالة رابعة، أو ترخيص Gemini Live.

## النقل المقترح للأدلة — بموافقة مسبقة

| البند في العقد | دليل محلي يُجمع في C1 | حدود الاستدلال |
|---|---|---|
| `run_url` | **`null` بوضوح**؛ رابط Issue #310 لتوثيق ملخص النتائج بعد المراجعة | ليس رابط GitHub Actions |
| `job_id` | **`null` بوضوح**، مع `local_process_id` لحالة واحدة في عملية Python مستقلة | PID ليس GitHub job ID |
| `head_commit_sha` | `git rev-parse '@'` قبل الحالات مع إثبات المصدر | HEAD معلن من بيئة المالك، وليس توقيع GitHub Runner |
| `source_git_blob_hashes` | SHA مثبت لعقد V3 وB1 وB0 Manifest وGemini Adapter، مع فحص مصادر الـ14 عبر B1 | لا يثبت عزلًا عالميًا للمستودع |
| `per_case_input_sha256` | SHA256 للطلب الثابت أو العطل الثابت | لا يُسجّل مفتاح أو payload هجومي نصيًا |
| `per_case_exit_code` | رمز B1 الأصلي (0 أو 2) أو حالة إيقاف Gemini الاصطناعي، بجانب Exit Code الخاص بمشغّل الشاهد | رمز فشل مصطنع ليس عطل Google |
| `per_case_validated_json_or_error_code` | سجل JSON مُعقم خارج المستودع | لا نقل ملفات إلى CI |
| `execution_counters` | counters داخل نطاق وظائف C1 الثابتة وحواجز رفض الأثر الجانبي | ليست telemetry على النظام كله |
| `owner_review` | اعتماد GitHub مستقل **بعد** مراجعة الشواهد | لا يغني عنه نجاح اختبارات C0 القديمة |

ملف إثبات واحد جديد لكل حالة، إنشاء حصري لا يسمح بالكتابة فوق شاهد قديم، وبصمة SHA256 منفصلة لكل ملف. لا توجد عمليات GitHub Actions حقيقية أثناء هذا القياس.

**ملاحظة نظامية:** هذا اختيار **بديل لوسيط الدليل** بسبب تعذر Runner، وليس ادعاء تحقيق الشرط الأصلي نفسه. عند اتخاذ قرار C1 يجب ذكر الاستثناء صراحة. في حال عدم موافقة المالك على هذا البديل، يظل `C1=BLOCKED_ON_HOSTED_RUN_EVIDENCE` حتى حل الفوترة، دون إعادة تعريف النتائج أو إخفاء غياب `run_url/job_id`.

## التوقيع المطلوب قبل الحالات

إن وافق المالك، يُوثق اختياره على [Issue #310](https://github.com/lijust/EREI-3.2/issues/310) قبل أي تشغيل C1، بالنص الآتي (دون أن يعد موافقة على النتائج):

```text
c1 owner pre-run evidence transport acceptance: due to confirmed github actions billing block, approve exactly three separately invoked owner-local offline c1 cases using source-pinned runner and one exclusive json witness per case. acknowledge github run_url and job_id will remain null, with explicit local process id, source head, sha256 and independent case logs. accept this as scoped local evidence only, not github-hosted ci; do not modify v3 input, oracle, thresholds or retry rules. c1 final pass remains subject to post-run owner review. no real gemini calls, docker, root or generated-code execution. ai_acceptance=block_ai_acceptance. stable_ready=false.
```

هذه موافقة على شكل الدليل **قبل معرفة النتيجة**، ولا تُغيّر عقد C0 v3 أو حالة بوابة C1 تلقائيًا.

## حالة التنفيذ

```text
FORMAL_GATES=13/16
C0=GATE_PASS
C1_RUNNER_SOURCE_READY=true
C1_OWNER_LOCAL_WITNESS_SUBSTITUTION=PROPOSED_PRE_RUN_OWNER_SIGNOFF_PENDING
C1_CASES_EXECUTED=0
C1_FORMAL_GATE=NOT_PASSED
C2/C3=NOT_STARTED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```
