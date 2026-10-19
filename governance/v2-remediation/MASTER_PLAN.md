# خطة تنفيذ إصلاحات EREI V2

تاريخ الخطة: 2026-10-19، بتوقيت Africa/Cairo. مرجع البرنامج هو [Issue #68](https://github.com/lijust/EREI-Engineering-Framework/issues/68)، وتبقى [Issue #31](https://github.com/lijust/EREI-Engineering-Framework/issues/31) المرجع الحاكم لترقية Stable. تُعرض لقطة التقدم في [EXECUTION_STATUS.md](EXECUTION_STATUS.md)، والقرارات في [DECISION_LOG.md](DECISION_LOG.md)، ومصادر الإثبات وحدودها في [EVIDENCE_INDEX.md](EVIDENCE_INDEX.md).

## 1. الهدف والنطاق المصرح به

الهدف هو إصلاح سلامة البيانات والتوافق وحدود التفعيل وجودة التقييم، ثم إثبات أثر V2 على الجودة والوقت والتكلفة. الأولوية لإصلاحات محددة قابلة للاختبار، مع استخدام المكونات الموجودة وتقليل تكرار العمل.

يسمح هذا البرنامج بتعديل المصدر والاختبارات والوثائق في فروع مستقلة، وإعداد Issues وPRs للمراجعة. لا يمنح إذنًا بتعديل السجلات الحية أو Framework pins، أو إصدار Stable، أو النشر في production، أو تغيير إعدادات GitHub والـrunners، أو توليد credentials، أو تشغيل paid AI workflows. تبقى ملفات المشروع المتزامنة تحت `sources/` مراجع للقراءة فقط.

الحكم الموروث من التدقيق هو أن V2 يحتاج إصلاحات قبل اعتماده. نجاح الإصلاحات محليًا لا يثبت تحسن الإنتاجية في التشغيل، ولا يثبت فعالية إنفاذ أمني لم يُنشر ويُتحقق منه.

## 2. خط الأساس

| المصدر | الهوية المثبتة عند بدء البرنامج |
|---|---|
| V1 Stable | `69079018606750312344cb3c648952b9ab72d35b` |
| Framework main | `72d49658524fbce6145783cd52297c53edbb2c95` |
| EREI-App-Google main | `6d32e7a14a4324dbdea228f695d6b75e0b8bd246` |
| EREI-3.2 main | `87d730ddc3547f863de2a6895e91f9b83e9c6e72` |
| PR #67، تحسين تشغيل CI | `69a2d6cfb3d42c70e467d1fd6fff283e817972bf`، كان مفتوحًا عند التحقق |

أثبتت إعادة الإنتاج رفض 116 سجلًا صحيحًا من V1 في App وسجلين صحيحين في 3.2 بسبب حساب fingerprint، وتغير عضوية مراجعات V1 عند ترتيب الأحداث، ووجود 35 سجل V2 في App دون ملفات immutable authority. توجد أيضًا أربع حالات تاريخية مستقلة في App يجب أن تبقى محجوبة حتى يصدر قرار موثق بشأنها. نجح المُصحّح القديم خطأً في قبول 13 إجابة متناقضة من 13 حالة Core، وأعيد إثبات رفض بوابة bootstrap في 3.2 لتغيير تطوير عادي.

هذه لقطة مصدر، وليست وصفًا دائمًا لـmain. يجب إعادة قراءة refs ونتائج PR على الـSHA المقصود قبل كل قبول أو دمج. معرفات Findings من F01 إلى F14 ثابتة؛ أما T00 إلى T16 فهي معرفات خطة التنفيذ الحالية، وقد تختلف عن ترقيم المهام المقترح في تقرير التدقيق.

## 3. المهام ومعايير القبول

كل مهمة تُسلّم من خلال PR محدود، أو دليل تشغيلي منفصل عندما يتطلب العمل صلاحية خارج المصدر. تشمل المراجعة سبب المشكلة، الاختبارات قبل الإصلاح وبعده، الـSHA الدقيق، المخاطر وطريقة الرجوع. الساعات أدناه تقديرات جهد هندسي، وليست مواعيد أو تكلفة مقاسة.

### M0 — تثبيت الحقيقة والخطة

**T00 — [#68](https://github.com/lijust/EREI-Engineering-Framework/issues/68) — P1، L1، 2–4 ساعات.** تثبيت refs وإعادة probes وربط Findings بالمهام، لتجنب إصلاح حالة تاريخية تغيرت. النطاق هو وثائق `governance/v2-remediation/` وأدلة baseline. القبول: ثلاث هويات مستودعات مثبتة، حالة PR #67 موثقة، ومهام قابلة للتتبع. لا تبعيات؛ الرجوع يقتصر على تصحيح الوثائق. الفائدة هي منع ازدواجية العمل والادعاءات غير المدعومة.

### M1 — توافق البيانات وثبات التاريخ

**T01 / F01 — [#69](https://github.com/lijust/EREI-Engineering-Framework/issues/69) — P1، L2، 4–8 ساعات.** سبب الخلل إدخال مفاتيح V2 في canonicalization الخاص بـV1. يُعدل `tools/task_learning.py` وتضاف fixtures ثابتة في `tools/tests/fixtures/task-learning-v1.json` واختبارات `test_task_learning_legacy.py`. القبول: قبول V1 الصحيح بالـfingerprints الأصلية، ورفض تعديل محتواه، وبقاء حقول V2 مرتبطة بالبصمة. لا تبعيات ولا إعادة كتابة لسجل قديم. الرجوع للكود فقط؛ الفائدة المقاسة المستهدفة هي صفر رفض خاطئ في مجموعة التوافق المعروفة.

**T02 / F02 — [#70](https://github.com/lijust/EREI-Engineering-Framework/issues/70) — P1، L2، 8–16 ساعة؛ يعتمد على T01.** السبب تطبيق cutoffs موضعية قديمة بعد ترتيب جديد للأحداث. يُعدل دمج الأحداث في `tools/task_learning.py` وتضاف `test_task_learning_order.py`. القبول: الحفاظ على ترتيب projection الموجود وعضوية المراجعات الجزئية والكاملة، وعدم اعتبار أول حدث V2 مراجَعًا تلقائيًا، ورفض الهوية المكررة المبهمة. تبقى authority checks فعالة. لا يستعيد الإصلاح ترتيبًا تاريخيًا مفقودًا؛ يحتاج ذلك دليلًا أصليًا. الرجوع للكود قبل التبني، مع إبقاء المصدر والمراجعات القديمة؛ الفائدة صفر إعادة إسناد لعضوية المراجعة في fixtures المعروفة.

**T03 / F03 — [#71](https://github.com/lijust/EREI-Engineering-Framework/issues/71) — P1، L2، 8–16 ساعة؛ يعتمد على T01 وT02.** توجد projections من V2 بلا سلطة immutable. النطاق الحالي هو `tools/plan_task_learning_migration.py` واختباراته و`runbooks/TASK_LEARNING_MIGRATION_PREFLIGHT.md`: planner للقراءة فقط يطبع JSON، ولا يملك وضع apply. يربط bytes الأصلية وGit blob hashes والترتيب، ويصف الملفات المقترحة فقط عندما تصح جميع المدخلات. القبول: يبقى App الفعلي `BLOCKED` بسبب الحالات الأربع؛ تحفظ fixtures الصحيحة الهويات وعضوية المراجعات؛ لا تتغير bytes المصدر؛ لا تُصلح بصمات قديمة تلقائيًا. الرجوع هو استبعاد تقرير الخطة؛ لا توجد migration حية ضمن المهمة. الفائدة تشخيص قابل للتدقيق، وليس إتمام ترقية بيانات App.

### M2 — حدود القدرات وتكامل المشاريع

**T04 / F04 — [#72](https://github.com/lijust/EREI-Engineering-Framework/issues/72) — P1، L2، 8–16 ساعة.** بعض مسارات router وLearning Review تستدعي Learning Operations قبل فحص activation. النطاق `tools/capability_activation.py` ونقاط دخول pattern/debt/LDO/effectiveness، و`workflows/router/` و`workflows/learning-review/` و`workflows/learning-to-development/`. يُستخدم resolver واحد قبل التنفيذ المباشر وغير المباشر. القبول: غياب adoption أو انتهاء صلاحيته أو اختلاف ref/version يمنع تنفيذ Candidate قبل آثاره؛ adoption صحيح يسمح؛ Core يستمر عند dormancy؛ توقفات الأمن وسلامة البيانات تبقى إلزامية. لا تبعيات؛ الرجوع للكود دون تعديل pins. الفائدة صفر استدعاء غير مصرح في مصفوفة الاختبار.

**T06 / F07 — [EREI-3.2 #173](https://github.com/lijust/EREI-3.2/issues/173) — P1، L2، 4–8 ساعات.** السبب تطبيق allowlist الخاصة بالتأسيس على جميع PRs. النطاق `.github/workflows/erei-framework-integration.yml` واختبارات مقاطع workflow الفعلية في fixtures معزولة. القبول: يمر PR عادي يجمع source وتوثيق التعلم في مشروع مؤسس، وتبقى تغييرات runtime محجوبة في bootstrap الأول، وتفشل حالات base أو ledger غير الصالحة. لا تبعيات؛ PR مستقل للمشروع. الرجوع للـworkflow السابق؛ لا تغيير pin أو بيانات. الفائدة إزالة حالة الحجب الخاطئ المثبتة.

### M3 — صلاحية التقييم

**T05 / F05 — [#73](https://github.com/lijust/EREI-Engineering-Framework/issues/73) — P1، L2، 16–32 ساعة.** الاعتماد على كلمات متوقعة يسمح بقرار مخالف. النطاق `evals/runner.py` والـschema والمجموعتان المطلوبتان وfixtures وadapter و`tools/exact_target_evidence.py`. المطلوب عقد actions منظم وstate reducer موثوق، وفحص الآثار المحظورة، واستخدام scorer نفسه في retained replay دون كشف expected answers للـruntime. القبول: تفشل العينات المتناقضة المعروفة الـ13، ويفشل action خاطئ أو state يزعمه الرد دون إثبات، ويُفحص القرار والآثار عبر output منظم؛ لا يُدّعى تفسير تناقضات prose حرة. لا تبعيات مصدرية؛ الرجوع للـschema والـsuites معًا دون تعديل أدلة RC التاريخية. التحسن المقاس محصور في مجموعة الهجمات المعروفة؛ reference oracle يبقى synthetic.

### M4 — موثوقية الأدوات وكلفة التحقق

**T07 / F10 — [#74](https://github.com/lijust/EREI-Engineering-Framework/issues/74) — P2، L1، 2–4 ساعات.** السبب قبول قيم عددية غير صالحة ثم وصف المقارنة بالثبات. النطاق `tools/learning_effectiveness.py` و`tools/tests/test_learning_effectiveness_validation.py`. القبول: رفض NaN وInfinity وbool والقيم السالبة أو خارج المجال المناسب، وفصل missing عن zero، وعدم إعلان comparability مع غياب المقياس الأساسي. لا تبعيات؛ الرجوع للكود دون تعديل القياسات التاريخية. الفائدة صفر قبول للمدخلات العددية غير الصالحة في corpus الاختبار.

**T08 / F11 — [#75](https://github.com/lijust/EREI-Engineering-Framework/issues/75) — P2، L1، 2–4 ساعات.** السبب بناء adapter command دون quoting لمسارات بها فراغات. النطاق `evals/tests/test_runner.py` و`evals/tests/test_reference_oracle.py` فقط. يستخدم الاختبار `subprocess.list2cmdline` على Windows و`shlex.join` على POSIX، دون shell. القبول: نجاح تشغيل adapter فعلي من مسار يحوي فراغات وUnicode على Windows، واختبار POSIX parser roundtrip. لا يُدّعى تشغيل POSIX ما لم يحدث. لا تبعيات؛ الرجوع test-only. الفائدة إزالة فشلي تشغيل معروفين، وليس زيادة جودة النموذج.

**T09 / F12 — [#76](https://github.com/lijust/EREI-Engineering-Framework/issues/76) و[PR #67](https://github.com/lijust/EREI-Engineering-Framework/pull/67) — P2، L2، 8–16 ساعة.** السبب تكرار push/PR وتكرار full suite على Python 3.12 في workflowين. يُراجع PR القائم أولًا ثم أي تعديل إضافي في `assurance-gate.yml` و`project-bootstrap-tests.yml`. القبول: حفظ إثبات main/release على المصدر الدقيق، وإلغاء PR runs المتقادمة فقط، وبقاء التغطية على 3.11 و3.12، وعدم تحول skip/cancel إلى قبول زائف. تُقارن jobs والانتظار والـrunner seconds لعينة متكافئة قبل/بعد. الرجوع للـworkflow مع تحديث trusted digest قبل أي سلطة إصدار. الفائدة المقدرة منفصلة عن التوفير المقاس.

### M6 — سلطة الإصدار وعمر الأدلة

**T10 / F06 — [#77](https://github.com/lijust/EREI-Engineering-Framework/issues/77) — P1، L3، 16–32 ساعة.** توثيق review لا يثبت أن صاحبه يملك سلطة إنفاذ مستقلة. النطاق `tools/assurance_enforcement.py` و`release_approval.py` و`release_assurance.py` واختبارات provenance. القبول: لا يكفي clean review أو declaration=true لإثبات enforcement؛ ولا تُحسب هوية شكلية أو نفس actor موافقة مستقلة. يبقى الوضع الحالي fail-closed. لا نشر أو مفاتيح ضمن المهمة؛ الرجوع لا يجوز أن يعيد مسار قبول سلطة غير مثبتة. الفائدة سد مسار latent false authorization.

**T11 / F08 وF13 — [#78](https://github.com/lijust/EREI-Engineering-Framework/issues/78) — P2، L3، 16–40 ساعة؛ يعتمد على T10.** يلزم مسار إيجابي حقيقي لـserver enforcement وإثبات مصدر التنفيذ وعزل runner. النطاق `assurance_enforcement.py` و`independent_actions_source.py` وAction pins والسياسة. يمكن إعداد العقد والاختبارات السلبية الآن؛ إعداد GitHub أو runner أو سلطة خارجية يحتاج قرار المالك وصلاحية منفصلة. القبول: رفض workflow بديل له الاسم نفسه أو مصدر no-op أو hash مختلف، وقبول المصدر والسياسة المعتمدين بعد تحقق حي مستقل، مع دليل isolation. الرجوع يعطل سلطة الإصدار ويعيد الحالة المحجوبة. لا يكفي شراء GitHub Pro وحده.

**T12 / F09 — [#79](https://github.com/lijust/EREI-Engineering-Framework/issues/79) — P2، L3، 16–32 ساعة؛ يعتمد على T10 وT11.** الاعتماد الدائم على artifact online وغير منتهٍ قد يعطل adoption أو rollback لاحقًا. النطاق `github_actions_artifact_provenance.py` و`stable_release_carrier.py` و`plan_framework_upgrade.py`. يُحدد receipt موثق تحت السلطة المختارة، مع فصل انتهاء التخزين عن revocation. القبول: تحقق archive أصيل بعد day 91 أو outage؛ رفض tamper أو revocation؛ وعدم قبول ZIP مجهول. الرجوع يعطل fallback ويحفظ bytes الأدلة. الفائدة استمرار التحقق دون تخفيف المصادقة.

### M7 — قياس أثر التعلم

**T13 / F14 — [#80](https://github.com/lijust/EREI-Engineering-Framework/issues/80) — P2، L2، 8–16 ساعة؛ يعتمد على T01 وT02 وT04.** اكتمال سلسلة التنفيذ لا يثبت تحسن النتيجة. النطاق عقود التعلم و`PROSPECTIVE_CYCLE_STATUS.json` وربط LDO. يُضاف سجل تدخل صغير باستخدام JSON الموجود: finding/root cause ثم LDO وimplementation SHA وadoption وcohort وeligible exposure وoutcome. القبول: merge وحده ليس improved؛ zero exposure ليس نجاحًا؛ unknown لا يتحول إلى zero؛ assessment الصريح منفصل عن legacy assumptions. الرجوع بإصدار للعقد دون إعادة كتابة التاريخ. الفائدة تمكين قياس recurrence لكل exposure والتكلفة لكل نتيجة موثقة.

**T15 — [#82](https://github.com/lijust/EREI-Engineering-Framework/issues/82) — P2، L2، 16–32 ساعة؛ يعتمد على T05 وT13 وT14.** إعداد benchmark متكافئ وفق القسم 7. النطاق dataset وconfiguration وhidden acceptance وعقد المقاييس. يمكن إعدادها دون استهلاك model credits؛ التشغيل المدفوع محجوب حتى اعتماد runtime وbudget. القبول: تثبيت المصدر والبيئة، عدّ جميع المحاولات والإخفاقات، مراجعة عمياء، ونشر النتائج وحدود عدم اليقين. الرجوع يوقف trial ويحفظ كل المحاولات؛ الفائدة قياس الفرق بدل توقعه.

### M5 وM8 — التأهيل والتبني

**T14 — [#81](https://github.com/lijust/EREI-Engineering-Framework/issues/81) — P1، L2، 8–24 ساعة؛ يعتمد على T01 وT02 وT03 وT04 وT05 وT07 وT08.** تأهيل Internal Release محدود على SHA مجمع ثابت وبيانات معزولة صحيحة، مع اختبار رجوع للكود والبيانات. القبول في checklist أدناه؛ لا P1 غير محلول يؤثر في النطاق المعتمد. T06 شرط لتجربة 3.2 إذا شملها النطاق، وليس شرطًا لتجربة Framework معزولة. بيانات App المتناقضة مستبعدة حتى معالجة موثقة. الفائدة تمكين قياس داخلي محدود، دون ادعاء Stable أو منح pin upgrade.

**T16 — [#31](https://github.com/lijust/EREI-Engineering-Framework/issues/31) — P1، L3، 8–24 ساعة؛ يعتمد على T10 وT11 وT12 وT14 وT15.** تجميد RC بعد اكتمال الإصلاحات، وتقييم genuine runtime للحالات الـ13، وأدلة موثقة وموافقات مستقلة ثم Stable. التبني اللاحق منفصل لكل مشروع. القبول: استيفاء بوابات #31 على target/tree محددين، ومعالجة App بقرار موثق قبل ترحيله، واختبارات تكامل ورجوع 3.2. لا تفويض حالي بالنشر أو تغيير pins. الرجوع يشمل الكود والبيانات مع حفظ الأحداث الجديدة وإجراءات revocation المعتمدة عند الحاجة.

## 4. ترتيب التنفيذ والجهد

المسار الحرج للتجربة الداخلية هو `T01 → T02 → T03 → T14`، ويلتقي عند T14 مع T04 وT05 وT07 وT08. يمكن تنفيذ T04 وT05 وT06 وT07 وT08 وT10 بالتوازي؛ يجب مراجعة تداخل T04/T07 وT05/T08 عند دمج التغييرات في نسخة التأهيل. تُدمج طبقة F01 قبل F02، ويعاد تحديد base والتحقق من exact head بعد أي تغيير.

| المرحلة | المهام | الجهد المقدر بالساعات |
|---|---|---:|
| M0 | T00 | 2–4 |
| M1 | T01–T03 | 20–40 |
| M2 | T04، T06 | 12–24 |
| M3 | T05 | 16–32 |
| M4 | T07–T09 | 12–24 |
| M5 | T14 | 8–24 |
| M6 | T10–T12 | 48–104 |
| M7 | T13، T15 | 24–48 |
| M8 | T16 | 8–24 |
| الإجمالي | T00–T16 | 150–324 |

التوازي يقلل الزمن المنقضي، ولا يلغي الجهد. لا تشمل هذه التقديرات انتظار المراجعات أو شراء خدمة أو إعداد سلطة خارجية واسعة؛ يحتاج البديل الخارجي تحليل تكلفة وصيانة مستقلًا قبل الالتزام به.

## 5. Internal Release: أقل نطاق مفيد وآمن

يمكن تأهيل Internal Release دون انتظار نشر سلطة Stable، بشرط عزله عن production والبيانات الحية والصلاحيات الحساسة. تظل سلامة البيانات وحدود activation إلزامية. لا يُستثنى خلل مؤثر بحجة أن الاستخدام داخلي.

- [ ] تثبيت aggregate SHA وتسجيل جميع الاختبارات والمراجعات عليه.
- [ ] نجاح golden V1 fixtures واختبارات عضوية المراجعة، دون تعديل أدلة تاريخية.
- [ ] نجاح planner على fixtures صحيحة؛ بقاء App الحقيقي `BLOCKED`؛ عدم وجود apply أو تغيير pin.
- [ ] إثبات deny قبل تنفيذ Candidate عند غياب authorization، مع استمرار Core وتوقفات الأمن والبيانات.
- [ ] رفض behavioral scorer للعينات المتناقضة المعروفة؛ تسمية المحاكاة وreference oracle بوضوح.
- [ ] نجاح اختبارات finite metrics ومسارات Windows، وإظهار حدود التحقق من POSIX.
- [ ] اختبار رجوع الكود والبيانات على نسخة معزولة، مع حفظ الهويات والأحداث الجديدة.
- [ ] لا صلاحية production ولا credentials ولا workflow مدفوع ضمن التجربة.
- [ ] مراجعة مستقلة للتغييرات دون P1 غير محلول داخل النطاق؛ قرار Internal صريح يحدد المستخدمين والمدة والبيانات المسموحة.

الحالة الحالية لهذه القائمة غير مكتملة؛ لا تمثل هذه الوثيقة موافقة Internal أو Stable. يحتاج التبني على بيانات مشروع حقيقية قرارًا منفصلًا بعد إثبات صلاحية migration والرجوع.

## 6. مسار Task Learning V2 Core Stable ثم التبني

1. إكمال إصلاحات المصدر المؤثرة، ثم اختيار سلطة إنفاذ واحدة. يُقيّم أولًا مسار حماية private repository المدعومة فعليًا بوصفه أبسط بديل محتمل. لا يُفترض أن الاشتراك يضبط bypass أو required reviews أو runner isolation تلقائيًا.
2. إذا اختيرت سلطة مستقلة، يجب إثبات custody وrotation وrevocation وreplay prevention والتنفيذ الحصري لدى consumer. لا يُنشأ هذا النظام لمجرد تجنب اشتراك دون مقارنة تكلفة الصيانة والمخاطر.
3. تثبيت target SHA/tree واحد بعد تغييرات workflow والمصدر، وربط scope والـworkflow digests والأدلة به. التغييرات اللاحقة تستلزم إعادة التحقق المتأثر، لا إعادة استخدام نتيجة لا تطابق المصدر.
4. بعد اعتماد configuration والميزانية، تنفيذ 13 حالة Core على runtime مستقل حقيقي باستخدام scorer المصحح، مع حفظ responses والهوية والإعدادات وإعادة scoring مستقلة.
5. تحقق enforcement والأرشيف وrollback، ثم موافقات architecture/security المستقلة على الهدف نفسه واستيفاء #31. لا يصبح green CI دليلًا على protected-branch enforcement.
6. بعد Stable، تُعد PR منفصلة لكل مشروع لتحديث pin وإجراء التحقق والرجوع. App يحتاج قرار anomalies وmigration مستقلًا؛ 3.2 يحتاج بوابة التكامل المصححة. لا يُشترط تبني مشروع قبل الترويج، لأن adoption بوابة لاحقة له.

Learning Operations تبقى Candidate مستقلة. يبدأ تبنيها لاحقًا بقدرة واحدة وتدخل محدد ومدة محدودة ومقياس exposure؛ لا تُفعّل الحزمة كلها بسبب وجود ملفاتها أو تحديث Framework pin.

## 7. benchmark متكافئ ومقاييس لا تكافئ إخفاء الفشل

يُجهز pilot من 12 مهمة ممثلة، لكل منها ذراع V1 وذراع V2 وتكراران: 48 تشغيلًا. تشمل المهام عيوبًا معروفة، تعديلات عادية، تعافيًا من verification failure، سياقًا ناقصًا، وقيودًا أمنية. تُختار من المشروعين وتُصنف حسب risk وworkflow family قبل التشغيل. هذا pilot للتحقق من المنهج وتقدير التباين، وليس حجمًا مضمونًا لإثبات تفوق إحصائي.

يُثبت model/version وruntime وOS وtool permissions وميزانية الوقت والتوكنز وproject SHA. تُشغّل الأزواج بترتيب عشوائي في workspaces نظيفة، مع hidden acceptance ومراجعة لا تعرف ذراع التنفيذ. يُحسب timeout والإخفاق والتدخل البشري وإعادة المحاولة ضمن النتائج والتكلفة. يمنع استبعاد المهمة بعد رؤية نتيجتها أو تحسين prompt لذراع واحد فقط.

| المقياس | التعريف والضبط | baseline المتاح |
|---|---|---|
| First-Candidate Success Rate | أول candidate يحقق acceptance المستقل ÷ جميع المهام المسندة؛ مع coverage | غير متاح |
| Independently Verified Completion Rate | إنجازات مقبولة مستقلًا ÷ جميع المهام؛ deferred ليس إنجازًا تلقائيًا | غير متاح |
| Defect-Driven Rework Rate | مهام أعيد العمل فيها بسبب defect موثق ÷ المهام material المقيمة؛ يفصل عن iteration مخطط | غير متاح؛ 22/29 في EPOCH-023 إشارة rework عامة |
| Rework Cycles per Material Task | الدورات المسجلة ÷ المهام material؛ تفصل assessments الصريحة عن الافتراضات القديمة | 47/29 = 1.6207 في EPOCH-023 فقط |
| Verification Escape Rate | مهام ذات escape موثق ÷ المهام المؤهلة مع نافذة متابعة ثابتة | العدد الخام 2 من 29؛ ليس مقارنة V1/V2 |
| Final Failed Task Rate | مهام terminal failed ÷ جميع المهام material؛ توضح deferred وblocked منفصلتين | 0/29 failed، مع 18/29 deferred في EPOCH-023 |
| Root-Cause Recurrence Rate | تكرار الآلية السببية نفسها ÷ eligible exposures بعد تدخل محدد | غير متاح؛ zero exposure ليس نجاحًا |
| Review Debt | عدد الأحداث material غير المراجعة وعمرها بعد trigger؛ لا يغير cutoff لتجميل النتيجة | EPOCH-024 فارغ في اللقطة؛ لا baseline للعمر |
| CI Runner Occupancy | مجموع مدة jobs لكل head متكافئ، مع عدّ matrix وattempts والانتظار منفصلًا | عينة PR #66: 655 ثانية |
| End-to-End Completion Time | elapsed حتى acceptance المستقل؛ median وp95؛ يفصل الانتظار البشري والـqueue | غير متاح |
| Cost per Verified Task | جميع تكاليف model/tools/CI والوقت البشري المتفق عليه ÷ الإنجازات المقبولة | غير متاح؛ تشمل تكلفة الإخفاقات |
| Activation Violations | تنفيذ Candidate دون authorization ÷ نقاط الدخول المختبرة أو التعرضات المؤهلة | خلل مصدر مثبت؛ الهدف في الاختبار صفر |
| Regression Escapes | عدد regressions بعد القبول خلال نافذة ثابتة، مع severity وexposure | غير متاح للبرنامج |

تُنشر الفروق المزدوجة وفواصل عدم اليقين وحجم العينة ونسب missing، ولا تتحول unknown إلى zero. لا تسمى rework rate أو verification-failure rate «دقة تنفيذ».

بعد pilot، تُختبر فعالية التعلم بتدخل واحد قابل للتتبع، ومهام holdout مؤهلة لمشكلته، ومقارنة capture-only بالتدخل المعتمد حيث يصلح التصميم. يُربط finding بـLDO ثم implementation وadoption وexposure وoutcome. لا يثبت قبل/بعد الخام السببية إذا تغير model أو risk mix أو البيئة. نجاح 75 synthetic reference checks أو اكتمال دورة adoption لا يثبت خفض الوقت أو التكلفة.

يجب مراجعة configuration وسقف التكلفة وشروط الإيقاف قبل أي تشغيل مدفوع. يمكن تجهيز الاختبارات والبيانات والعقد الآن دون model credits.

## 8. برنامج تقليل التعقيد

| المكون | القرار | التغيير الأدنى والحد الذي يجب حفظه |
|---|---|---|
| Constitution وسياسات المخاطر | KEEP | حفظ حدود الملكية؛ تجنب موافقة إضافية لكل خطوة منخفضة المخاطر |
| Roles وrouter | SIMPLIFY | resolver واحد قبل entrypoints؛ فصل التوجيه الاختياري عن توقفات الأمن |
| Project context وoverlays | KEEP | تبقى مملوكة للمشروع ومحايدة تجاه runtime؛ لا تعديل pin ضمن الإصلاح |
| Task Learning وimmutable authority | KEEP | إصلاح V1 canonicalization والترتيب؛ لا إلغاء provenance لتسهيل migration |
| Python وproject JS validation | CONSOLIDATE | fixtures مشتركة وعقد واضح أولًا؛ لا shared service جديد |
| Pattern وdebt وLDO | SIMPLIFY | activation صريح؛ pure validation منفصل عن project execution |
| Effectiveness وdashboard | SIMPLIFY | سجل intervention/exposure صغير وrenderer بسيط؛ لا analytics platform جديدة |
| Behavioral scoring | REFACTOR | actions وعقد state deterministic؛ scorer واحد للتشغيل وretained replay |
| Release review والسلطة | REFACTOR | فصل هوية review عن سلطة القبول والإنفاذ؛ default يبقى deny |
| External signing infrastructure | DEFER | لا نشر قبل اختيار السلطة وإثبات الحاجة والتكلفة |
| Evidence retention والتحقق | CONSOLIDATE | سياسة receipt وrevocation واحدة بعد تثبيت authority contract |
| Push/PR duplicate runs | REMOVE | الاستفادة من PR #67 مع حفظ إثبات main/release والمصدر الدقيق |
| Full suite المكررة على 3.12 | CONSOLIDATE | مرة لكل interpreter مع بقاء دعم 3.11 و3.12 |
| قواعد review debt المتكررة في الوثائق | SIMPLIFY | عقد واحد تُحيل إليه workflows؛ لا defer يتجاوز security/data blocker |
| إدارة مهام إضافية | DEFER | GitHub Issues/PRs هي المرجع؛ الوثائق لقطات مؤرخة، لا قاعدة حالة موازية |
| Runtime أو evaluation platform جديدة | REUSE | استخدام runtime قائم؛ تقييم Promptfoo أو منصة ناضجة عند حاجة محددة، لا إعادة بناء tracing/storage عام |
| Stable gate وrollout لكل مشروع | KEEP | #31 للترويج، ثم PR واختبار ورجوع مستقلان لكل consumer |

عينة PR #66 تسمح بتقدير مضاد للواقع: إزالة تشغيل مكرر مدته 178 ثانية من 655 تعادل 27.2% من runner occupancy؛ وعدد workflows من 3 إلى 2 وjobs من 4 إلى 3. هذا تقدير لعينة واحدة، وليس وفرًا مقاسًا بعد التطبيق أو ضمانًا لزمن PR. توجد نحو 132 ثانية إضافية في full suite المكررة على 3.12 في عينة الخطوات، ويجب إعادة قياسها بعد التصميم المقترح وعدم جمع النسب بلا نموذج workload متكافئ.

لكل مكون جديد يلزم بيان المشكلة المثبتة، ولماذا لا يكفي مكون قائم، وكلفة الصيانة، والبديل الأبسط، ومقياس نجاح. حذف أسطر أو وثائق ليس هدفًا بذاته؛ يجب الحفاظ على invariants قبل إزالة التكرار.

## 9. حالة العمل والقبول والرجوع

`BACKLOG` عمل غير جاهز؛ `READY` نطاقه ومعايير قبوله معروفة؛ `IN_PROGRESS` بدأ؛ `IN_REVIEW` له PR منشورة. `VERIFIED` يتطلب اختبارات ومراجعة مستقلة على exact head؛ `DONE` يتطلب تسليمًا أو دمجًا متحققًا. `BLOCKED` له سبب محدد؛ `DEFERRED` يحتاج قرارًا معللًا. checkpoint محلي ناجح لا يساوي PR منشورة أو تغييرًا في main.

الأوزان المرجعية هي منتصف ساعات كل مهمة في خطة التنفيذ، ومجموعها 237. تقدم التسليم = مجموع أوزان DONE ÷ 237؛ تعرض VERIFIED منفصلة. لا تصبح readiness الأمنية نسبة مئوية، ولا يُحسب إنشاء الوثائق تحسنًا في المنتج. يسجل تغيير النطاق أو الوزن في Decision Log بدل إعادة تعريف التقدم بعد رؤية النتيجة.

تُشغّل اختبارات العيب المحددة أثناء التطوير، ثم التحقق المجمع المناسب قبل التأهيل. لا تُجرى اختبارات تولد signing keys ضمن هذا التفويض. مراجعة agent مستقل للمصدر مفيدة، لكنها لا تعادل independent release authority.

الرجوع عن إصلاح مصدر يتم عبر revert مراجع. تغييرات schema والـscorer مترابطة ويجب الرجوع عنها معًا. أي migration لاحقة تحتاج نسخة أصلية موثقة، وإعادة فحص digests، وكتابة غير مستبدلة للسجلات immutable، وفحص الهويات وعضوية المراجعات قبل/بعد، ومسار رجوع يحفظ الأحداث الجديدة. هذه الشروط لا تمنح إذن التنفيذ الحي.
