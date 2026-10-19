# فهرس الأدلة — EREI V2

لقطة 2026-10-19، Africa/Cairo. هذا الفهرس يميز بين source identity واختبارات محلية وCI رسمي وبين authority تشغيلية. مراجعة agent للمصدر لا تصبح جهة إصدار مستقلة.

## المصادر الدائمة

| المصدر | الرابط / الهوية | ما يثبته |
|---|---|---|
| Framework main | [commit](https://github.com/lijust/EREI-Engineering-Framework/commit/72d49658524fbce6145783cd52297c53edbb2c95) | المصدر الأساسي؛ tree `79e175f36dfc590b6da610f3609c939380965a15` |
| V1 Stable | [commit](https://github.com/lijust/EREI-Engineering-Framework/commit/69079018606750312344cb3c648952b9ab72d35b) | canonicalization المرجعي |
| App | [commit](https://github.com/lijust/EREI-App-Google/commit/6d32e7a14a4324dbdea228f695d6b75e0b8bd246) | نسخة أدلة التعلم؛ ليست موافقة migration |
| 3.2 | [commit](https://github.com/lijust/EREI-3.2/commit/87d730ddc3547f863de2a6895e91f9b83e9c6e72) | baseline تكامل المشروع |
| Scope وترقية Stable | [Issue #31](https://github.com/lijust/EREI-Engineering-Framework/issues/31) | متابعة البوابات؛ لا موافقة جديدة |
| البرنامج | [Issue #68](https://github.com/lijust/EREI-Engineering-Framework/issues/68) | ربط المهام والتبعية والحالة |
| CI قائم | [PR #67](https://github.com/lijust/EREI-Engineering-Framework/pull/67) | اقتراح تقليل التكرار؛ ليس وفرًا مقاسًا |

## الرؤوس المنشورة وأوامر إعادة الاختبار

- **F01**: [PR](https://github.com/lijust/EREI-Engineering-Framework/pull/83)، head `6054baf7f9b926203d47f94db1adf909810b88ef`. اجتاز 29 اختبارًا محددًا مع إعادة تشغيل مستقلة. بقيت أربع anomalies تاريخية في App محجوبة دون تعديل.
- **F02**: [PR](https://github.com/lijust/EREI-Engineering-Framework/pull/84)، head `3545df37a90695a588ce5ced4a5a1327ea3d803d`. بعد ملاحظة المراجعة المستقلة، أضيف رفض فقد ترتيب projection مع legacy reviews. اجتاز الرأس الحالي 37 اختبارًا؛ F03 فوقه اجتاز 48 اختبارًا. لم يُعد بناء تاريخ مفقود بالتخمين.
- **F03**: [PR](https://github.com/lijust/EREI-Engineering-Framework/pull/88)، head `9ca0fd14ca2e4a60def23f9e7df11c827a961135`. اجتاز 48 اختبارًا مع تبعياته. App: BLOCKED، و35 سجلًا بلا authority وأربع anomalies؛ لا proposed writes. 3.2: NO_IMPORT_REQUIRED. هذا تسليم planner فقط.
- **F04**: [PR](https://github.com/lijust/EREI-Engineering-Framework/pull/86)، head `0555feb863412db1032b229c48073b2a9eb83479`. اجتاز 62 اختبارًا محددًا وأربع standalone scripts. الفحص التنفيذي يخص نقاط دخول Python؛ Markdown سياسة للـagent ولا يُعد سلطة إنفاذ مستقلة.
- **F05**: [PR](https://github.com/lijust/EREI-Engineering-Framework/pull/89)، head `0b2f9a517215a5b0070617e9c9312c6377d0c218`. اجتاز 52 اختبارًا محددًا، و75 reference cases اصطناعية. الدمج المعزول مع F11 اجتاز 78 اختبارًا. عقد output منظم؛ لا natural-language judge ولا تشغيل نموذج حقيقي.
- **F07**: [PR](https://github.com/lijust/EREI-3.2/pull/174)، head `50cc659415af535e1b20a45a3a2453d0aa07afa3`. اجتاز 13 اختبارًا يعيد تنفيذ مقاطع workflow الفعلية في مستودعات Git مؤقتة. لا تغيير pin أو بيانات أو application code.
- **F10**: [PR](https://github.com/lijust/EREI-Engineering-Framework/pull/87)، head `e779b5fdaa347665355e89439b72820313dfcf20`. اجتازت الاختبارات العددية التسعة وgovernance script، مع مراجعة مستقلة. الدمج مع F04 اجتاز 25 اختبارًا. PR مبني على F04 ويحفظ activation guard.
- **F11**: [PR](https://github.com/lijust/EREI-Engineering-Framework/pull/85)، head `084c3ab0bf0dd9e5afcadf074c723533fe190561`. اجتاز 65 اختبار eval؛ المراجع المستقل أعاد 11 اختبارًا في الملفين المعدلين. POSIX parser فقط، وليس POSIX runtime.

تُشغّل الأوامر التالية من checkout للرأس المناسب، على بيانات fixtures فقط:

```text
python -B -m unittest tools.tests.test_task_learning tools.tests.test_task_learning_legacy -v
python -B -m unittest tools.tests.test_task_learning tools.tests.test_task_learning_legacy tools.tests.test_task_learning_order -v
python -B -m unittest tools.tests.test_task_learning tools.tests.test_task_learning_legacy tools.tests.test_task_learning_order tools.tests.test_plan_task_learning_migration -v
python -B -m unittest tools.tests.test_task_learning tools.tests.test_capability_activation tools.tests.test_learning_operation_activation -v
python -B -m unittest tools.tests.test_learning_effectiveness_validation tools.tests.test_learning_operation_activation -v
python -B -m unittest evals.tests.test_behavioral_simulation evals.tests.test_copilot_cli_exact_target evals.tests.test_copilot_routing_prompt_boundary tools.tests.test_exact_target_evidence -v
python -B -m unittest discover -s evals/tests -v
python -B tests/test_framework_integration_gate.py -v
```

السطر الأخير خاص بمستودع 3.2. الأمر الكامل لـevals على F05 منفردًا يصطدم بفشلي F11 المعروفين على Windows؛ عينة الدمج مع F11 اجتازت 78 اختبارًا. لا تُعرض عينة الدمج بوصفها CI لرأس منفرد. لا تستدعي هذه الأوامر نموذجًا مدفوعًا، ولا ينبغي توسيعها إلى اختبارات تولد مفاتيح ضمن التفويض الحالي.

## الأدلة المحفوظة خارج المستودع

حُفظ التدقيق السابق باسم `EREI-V2-Independent-Audit-AR.md` ومعه `EREI-V2-Audit-and-Evidence.zip` في مساحة مخرجات المحادثة. وحُفظت checkpoints البرنامج تحت `erei-v2-remediation-2026-10-18/evidence/`: `data-f01` و`data-f02` و`data-f02-repair` و`data-f03` و`eval-f05`، مع نسخ المصدر وpatches وdigests ونتائج محلية. تحفظ نسخة activation في `verification/activation/checkpoint.json` وسجلات checks.

هذه مخرجات محلية مساعدة؛ لا تُعامل بوصفها GitHub attestation أو أرشيف إصدار مستقل. المرجع الدائم للمصدر هو commit المنشور، وتُعاد الاختبارات من ذلك المصدر. يلزم ربط نتائج CI الرسمية بالرأس نفسه قبل إغلاق المهام. لم تُنشر بيانات المستهلكين الخام في Framework.

## نتيجة CI المتاحة

رأس #83 `6054baf7f9b926203d47f94db1adf909810b88ef` أعاد عمليتي run `39185654385` و`39185680855` بنتيجة `startup_failure`، وjob count = 0. تعذر استرجاع check-suite details عبر connector. لا سبب جذري مؤكد ولا CI PASS. يجب قراءة السبب في GitHub أو بوسيلة مصرح بها ثم معالجة السبب وإعادة التحقق؛ لا تعديل إعدادات أمني تلقائي.

## حدود الاستنتاج

لا توجد مقارنة V1/V2 متكافئة منفذة، ولا قياس cost per verified task، ولا دليل causal على خفض rework أو escapes. اكتمال دورة prospective القديمة يثبت انتقال findings وتنفيذ adoption في نطاقها، ولا يثبت أثرًا بعد exposure كافٍ. لا يعد EPOCH-024 الفارغ تحسنًا. تبقى المقاييس المفقودة unknown، ولا تعاد كتابة التاريخ لتوليد baseline مرغوب.
