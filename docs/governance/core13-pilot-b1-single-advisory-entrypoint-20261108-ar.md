# Core13 PILOT-B1 — نقطة دخول استشارية واحدة، بدون تنفيذ

**8 نوفمبر 2026 | B1 implementation candidate — NOT FORMALLY CLOSED.**  
مراجعة B0 المعتمدة: [Issue #309 / comment #6713825884](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6713825884). الحزمة A مغلقة `CLOSED_PASS_SCOPED_READ_ONLY`.

## الهدف وحد النطاق

بناء **CLI واحدة** `tools/core13_pilot_b1_advisory_only.py` لا تملك سوى قراءة بيانات مراجعة المسارات الـ14 المثبتة، وإرجاع **توصيات تصنيف** `inspect_route` أو **حدود تشغيل** `guardrails`، دون استيراد أو استدعاء أي محرك تنفيذ.

هذا عمل استشاري ثابت المصدر **وليس نموذج AI متصلًا**، ولا يستخلص فعالية تعلم أو مراجعة كود آلية. هو نقطة دخول Pilot قابلة للتشغيل/المراجعة بحدود واضحة. نتوقف عند المطلوب بدل بناء منصة تنفيذ جديدة.

## واجهة الاستخدام المغلقة

```text
python -m tools.core13_pilot_b1_advisory_only --project-root <repo> --request-json '{"operation":"guardrails"}'
python -m tools.core13_pilot_b1_advisory_only --project-root <repo> --request-json '{"operation":"inspect_route","route_id":"J4_DIRECT_HOST_DOCKER"}'
```

- المدخل **JSON واحد** بحد 1024 بايت، يرفض مفاتيح مكررة وحقول غير معروفة ومحارف تحكم وعملية غير مدرجة.
- `guardrails` لا يقبل غير `operation`، و`inspect_route` يقبل فقط `operation` و`route_id` من القائمة المغلقة **14**.
- لا يقبل Paths من المستخدم، ولا Shell أو Python Code أو Model Prompt أو Patch أو URLs أو تعليمة Container. الرفض خروج `exit=2` مع رسالة ثابتة لا تعيد طباعة المدخل.
- يقرأ Manifest B0 ثابتًا ببصمة Git blob `814e7194dc5ebd95557616a68117138ee880da3e` ويعيد فحص بصمات **الملفات الـ14 الفعلية** قبل أي تقرير. تغيير أي مصدر = Fail closed.
- يستورد من المكتبة القياسية فقط `argparse`, `hashlib`, `json`, `pathlib`, `stat` ولا يستورد `subprocess`, `socket`, `docker`, `os` أو أي مكون J4/J4S/F5/Root/Framework. لا يوجد `eval` أو `exec` أو ديناميكية Imports.
- Outputs تتضمن دائمًا: `model_calls=0`, `docker_api_calls=0`, `shell_calls=0`, `network_calls=0`, `root_calls=0`, `patches_written=0`; و`stable_ready=false` و`AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE`.

## حدود الإثبات والاعتماد

1. يجب أن تعمل CLI فعلًا في GitHub Actions Nonroot، وأن تنجح `guardrails` و`inspect_route` المسموحتان.
2. يجب أن تفشل سلبًا أوامر `execute` و`docker` و`apply_patch` وأي URL/Code/Path/Unknown Route/JSON malformed أو مكرر؛ لا استثناء لحالة اسم مسار قديم.
3. يجب تثبيت كود CLI والـSource Manifest والاختبارات ببصمات SHA، وفحص Imports AST وعدم وجود API أو دوال تنفيذ Host.
4. يجب الإقرار بأن هذا **مدخل استشاري واحد مسموح**، وليس ضمان إغلاق كل أبواب التشغيل القديمة من بقية CLI المستقلة أو Github Workflows. وصول B1 المنفصل إلى J4/J4S غير موجود في Import Graph، لكنه **ليس عزلًا عالميًا للمستودع**.
5. **B1 GATE_PASS** يتطلب رابط CI/Job/Logs + أدلة رفض فعلية + مراجعة اعتماد مالك بعد التشغيل في [Issue #309](https://github.com/lijust/EREI-3.2/issues/309). نجاح الاختبارات وحده = `B1_PRE_REVIEW`.

## B2 وB3 دون Overengineering

- **B2:** كتابة خريطة الوصول والتبعيات لباب B1 فقط، وثيقة ترحيل/Rollback لنقطة الدخول إلى حالة `DENY`، وعدم حذف J4/J4S لأنهما آثار تجريبية خارج الباب. تجميع الاختبارات في CI واحدة؛ لا إعادة بناء Root Proxy.
- **B3:** تقرير إغلاق للحزمة B يوضح ما أثبتناه وما لم نثبته، واعتماد المالك، ثم فتح حزمة C للاستعراض الاستشاري المحدود.

تظل `stable_ready=false`، `AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE`، `INDEPENDENT_TERMINAL_SETTLEMENT=NOT_ESTABLISHED`، ولا يُسمح بتنفيذ أكواد يولدها نموذج.
