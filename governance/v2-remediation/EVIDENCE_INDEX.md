## تحديث دليل التنفيذ — 2026-10-23 (الأقسام السابقة تاريخية)

| محور الدليل | المصدر الثابت | نطاق الإثبات وحدوده |
|---|---|---|
| final main / source | [commit](https://github.com/lijust/EREI-Engineering-Framework/commit/58034ae3e6eca6b2e45f79453aa71a783beee07c)؛ tree `928a622cfa5b027b7f77d1b0599b22c36acd28a9` | ستة مسارات جديدة مدمجة؛ مطابق bytes للمصدر المختبر، لكن ليس release provenance تلقائيًا |
| source matrix 3.11 | [Actions #39889369608](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/39889369608) | exact checkout `e9562046b80d194316653b7e98e13f16bb0437d3`؛ 448 tool +80 eval PASS |
| source matrix 3.12 | [Actions #39888381351](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/39888381351) | 448 tool +80 eval PASS لنفس source tree |
| final-main source SHA CI | [Assurance #39913519288](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/39913519288)، [Bootstrap #39913519322](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/39913519322) | **SUCCESS** على `58034ae3...`: Assurance **448 tools+80 eval**، Bootstrap **448 tests على 3.11 و3.12**؛ readiness صريح `stable_ready=false`. [Ubuntu #39913519253](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/39913519253) failed مع صفر test steps، السبب غير مثبت. أي documentation merge ينتج SHA جديدًا يحتاج تمييزًا عن هذا الدليل. |
| T14 isolated rollback | [PR #94](https://github.com/lijust/EREI-Engineering-Framework/pull/94)، [Actions #39918441589](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/39918441589) | **4/4 PASS لكل Python 3.11 و3.12** مع V1 source hash مثبت وGit checkout نظيف؛ اختبار استعادة ملفات مصطنعة، لا تشغيل App، PR ما زال DRAFT، Internal NOT QUALIFIED. |
| F02 / F03 / F04 P1 | [#84](https://github.com/lijust/EREI-Engineering-Framework/pull/84)، [#88](https://github.com/lijust/EREI-Engineering-Framework/pull/88)، [#86](https://github.com/lijust/EREI-Engineering-Framework/pull/86) | original threads unresolved، `COMMENTED` فقط؛ الإصلاحات مدمجة، القبول المستقل معلق |
| App data | [#68](https://github.com/lijust/EREI-Engineering-Framework/issues/68) | 35 V2 مع missing immutable و4 anomalies؛ source guards لا تعني data recovery |
| release authority | [#31](https://github.com/lijust/EREI-Engineering-Framework/issues/31) | `main.protected=false`، 0/13 exact-target model cases، enforcement/approvals incomplete، Stable BLOCKED |
| learning outcomes | [PR #93](https://github.com/lijust/EREI-Engineering-Framework/pull/93) | declared exposure only، `effectiveness=NOT_ESTABLISHED`، ولا قياس وفورات وقت/تكلفة |

**أعداد الاختبارات متداخلة وليست 1,056 حالة فريدة.** [#68](https://github.com/lijust/EREI-Engineering-Framework/issues/68) يعرض حالة التنفيذ، وهذا الفهرس يحتفظ بالـhistorical SHA refs الواردة أدناه كما هي، مع وسمها كلقطات مؤرخة.

---

## فهرس الأدلة السابق — لقطة تاريخية

# فهرس الأدلة — EREI V2

سجل متتابع؛ آخر دفعة 2026-10-21، Africa/Cairo. الفقرات المؤرخة السابقة تاريخية ويعلوها آخر تحديث. هذا الفهرس يميز بين source identity واختبارات محلية وCI رسمي وبين authority تشغيلية. مراجعة agent للمصدر لا تصبح جهة إصدار مستقلة.

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

لقطة 2026-10-19 على رؤوس #83–#91 الحالية: 19 محاولة startup_failure و0 jobs في جميعها. لا تتوفر تفاصيل السبب عبر connector. لا CI PASS ولا نسبة إلى billing أو YAML أو runner دون دليل. المعرّفات والرؤوس والنتائج محفوظة في [verification-20261019.json](evidence/verification-20261019.json).

## حدود الاستنتاج

لا توجد مقارنة V1/V2 متكافئة منفذة، ولا قياس cost per verified task، ولا دليل causal على خفض rework أو escapes. اكتمال دورة prospective القديمة يثبت انتقال findings وتنفيذ adoption في نطاقها، ولا يثبت أثرًا بعد exposure كافٍ. لا يعد EPOCH-024 الفارغ تحسنًا. تبقى المقاييس المفقودة unknown، ولا تعاد كتابة التاريخ لتوليد baseline مرغوب.

## دفعة التحقق المجمع وF06/F12

- F06: [Draft #91](https://github.com/lijust/EREI-Engineering-Framework/pull/91)، head 106181a254e72b23f950e05d435b7e00b5a354fe؛ 49 اختبارًا محليًا. مراجعة مستقلة معلقة، ولا positive authority path.
- F12: [Draft #92](https://github.com/lijust/EREI-Engineering-Framework/pull/92)، head a42f9413a98d829ce51b48bed38d7294f931bae3؛ 41 اختبارًا على كل من Python 3.11 و3.12. بني فوق PR #67، tree الأصل beaf9e612c2f2aecc4ccd50f5712cbe76e6e5b11؛ 307 blobs غير معدلة طابقت الأصل.
- تجميع #83–#89 و#91: 144 tool tests + 78 eval tests = 222، وأربع standalone scripts ناجحة. SHA-256 لكل ملف متغير وأوامر المجموعات في سجل التحقق. ليس commit إصدارًا؛ يجب إعادة qualification على SHA ثابت بعد المراجعة.
- طابقت 52 مقارنة Git blob الملفات المعدلة المنشورة في عشرة PRs المصدرية؛ لا mismatches. لا تجمع أعداد الاختبارات المتداخلة كاختبارات فريدة.

أمر F12، مع تكراره على -3.12:

```text
py "-3.11" -B -m unittest tools.tests.test_ci_test_partition tools.tests.test_ci_event_dedup_contract tools.tests.test_bootstrap_project tools.tests.test_capability_activation -v
```

## أدلة 2026-10-20 — تحل محل الادعاء الحالي للرأس السابق فقط

[سجل الدفعة](evidence/verification-20261020.json) يحفظ 193 tool tests و78 eval tests على تجميع مصدر معزول، وهويات 50 ملفًا متغيرًا. ليس release target مجمدًا.

- #91 الحالي: a132e104c6881d7dc4f1002862741bc33a0da748؛ 73 اختبارًا. فشلت حالتا readiness قبل الإصلاح ثم نجحتا. نتائج 49 اختبارًا السابقة تاريخية.
- #93: 85ead2121ecb03454495200a475ca9f3f129398e؛ 50 اختبارًا على 3.11 و3.12، وgovernance standalone ومثال العقد ناجحة. 306 blobs غير معدلة تطابق parent #87، وخمسة ملفات منشورة تطابق المصدر المختبر.
- Cycle complete بقي كما هو؛ المخرج يوضح DECLARED_STEP_REFERENCES وeffectiveness=NOT_ESTABLISHED، دون تعديل ملف الدورة.
- سبب billing للمحاولة 39185680855 من نص Annotation الذي نقله المالك، وليس قراءة بيانات الحساب أو تحققًا مستقلًا من سبب بقية المحاولات. لم تتغير settings أو spending limits.
- المراجعة المستقلة وCI الرسمي معلقان؛ الأعداد المتداخلة لا تجمع.

## إعداد T14 / rollback — 2026-10-20

- [Draft #94](https://github.com/lijust/EREI-Engineering-Framework/pull/94)، head a20cccf9447b46bc87e38b568bae5662c84acf02، tree 49fb8a5e0ae6cc8dfe8071bae75283901ea2fcdf؛ فوق #88.
- 3 حالات على كل من Python 3.11 و3.12 و48 regression tests؛ 315 ملفًا منشورًا مطابقًا للنسخة المختبرة.
- [سجل مستقل لهذه الدفعة](evidence/verification-rollback-20261020.json)؛ لا يغير أدلة التجميع السابق أو يدعي Internal qualification.
- إثبات استعادة baseline مع بقاء أرشيف V2 كاملًا وعضوية المراجعات والتنبيه المعلق؛ ليس downgrade in-place أو reconciliation تلقائيًا.

## إعداد T15 الأولي / benchmark — لقطة تاريخية 2026-10-20

- [Draft #95](https://github.com/lijust/EREI-Engineering-Framework/pull/95)، head b6d421c03b5d0f4967c524a15fd734f9759fe758؛ tree 11177ce326f3ec7160931f64a4563008bd23e5e9.
- [السجل](evidence/verification-benchmark-20261020.json): 17 اختبارًا على Python 3.11 و3.12؛ CLI جاف بـ48 slot وصفر observations؛ 311 published blobs و12 reference blobs مطابقة.
- المصدر public calibration proposals؛ fixture/prompt/hidden acceptance غير مجهزة. لا consumer tests أو model executions أو paid AI أو دليل effectiveness.

## معايرة T15 — مصدر 2026-10-20، متابعة 2026-10-21

- [Draft #95](https://github.com/lijust/EREI-Engineering-Framework/pull/95): head cf6fd76635f4417137b2babc5e1fc28a7291b95a؛ tree d89f51e2d5d79cfcdbc802cd2323dbc172fba792. طابقت 314 published blobs النسخة المختبرة، وبقيت 13 consumer input blobs دون تغيير.
- [الأدلة](evidence/verification-calibration-20261020.json): 27 unit tests على كل Python 3.11/3.12؛ ست معايرات مع Node 24.20.0. لكل إصدار: 3 Node scripts و16 Python functions مرجعية ناجحة؛ mutants الست تفشل في assertions المتوقعة.
- public calibration فقط؛ لا paid AI أو hidden acceptance أو comparative result. ست مقترحات باقية، والمراجعة المستقلة معلقة.
- CI في السجل يخص 20 أكتوبر؛ لا يُستخدم لإثبات استمرار عائق الفوترة بعد إفادة المالك يوم 21 أكتوبر. وافق المالك على إعادة CI العادي لاحقًا؛ رفض GitHub إعادة المحاولة القديمة بـ403 لأنها غير قابلة للإعادة. لا نتيجة تشغيل جديدة حتى هذه اللقطة.

## قبول المصدر واستئناف CI — 2026-10-21

- [نتائج CI](evidence/ci-recovery-results-20261021.json): 18 workflow runs، منها 17 نجاحًا و21 jobs ناجحة؛ workflow Ubuntu واحد ممنوع بالفوترة قبل التنفيذ. يشمل الرأس المصحح لـ#95 وCI ناجحًا له.
- ربط checkouts بـGit trees يثبت تطابق source content مع الرؤوس، ولا يحوّل merge SHA إلى HEAD نفسه.
- [المراجعات المستقلة](evidence/independent-source-reviews-20261021.json): #91 و#92 و#93 و#94 كاملة في نطاقها؛ #95 narrow delta فقط، أما الكتالوج الكامل و#88 الجديد فلم يكتمل قبولهما.
- T08 وT10 صارا VERIFIED source-only بعد المراجعة وCI؛ DONE=0، ومجموع وزن VERIFIED=27/237 منفصل عن وزن DONE=0/237. لا صلاحية إصدار أو deployment.
- [تصحيح assertion](evidence/verification-calibration-20261021.json): رأس #95 الجديد da9b5160d8fc9789fb878683b24d3f287e759483، tree6842fc1ce6834fd2f70d62c3a8fb400c8a671349؛314blobs مطابقة،28tests وست معايرات لكل Python version. Plan digest السابق لم يتغير.
- السبب الحالي لـUbuntu مثبت من API annotations لوظيفتي118970186983 و118970187171 في run39522736910. لا حاجة لتخمين السبب أو نسبته إلى Copilot. لا تعديل حساب أو استبدال Linux بWindows.
- نتائج75reference cases اصطناعية؛ genuine exact-target model cases=0/13، Stable=false.

## متابعة 2026-10-22 — نتائج أحدث دون إعادة كتابة التاريخ

- [أدلة التسليم وCI](evidence/verification-delivery-20261022.json): main64f9بعد#85، ورأس#88، ورأس#95d622؛ ستةworkflows وسبعjobs ناجحة، معtestcounts وcheckout/head tree bindings.
- [المراجعات المستقلة الجديدة](evidence/independent-source-reviews-20261022.json): اكتمال مراجعة#88، والإعداد الكامل السابق لـ#95، وإضافةAPP03؛ وحدودAPP04. السجل السابق يحتفظ بموقفه وقت إنشائه.
- [معايرةAPP03](evidence/verification-app03-20261022.json): 93evaltests على كلPython3.11/3.12،7reference/mutant pairs،19inputblobsunchanged؛314publishedblobs مطابقة. plan909f427b…؛48slots وصفرobservations.
- T05/T08=DONE،T03/T10=VERIFIEDsource-only؛ أوزانDONE27/237 وVERIFIED36/237. لاقياسcausal لتوفيرCI أوeffectiveness، ولاgenuine13-case evidence. الحالة الحية في[EXECUTION_STATUS.md](EXECUTION_STATUS.md) وIssue#68.

- [تصحيح F05-R1 وتسليمه](evidence/verification-f05-reason-20261022.json): RED ثماني حالات، GREEN80evaltests لكل إصدار، مراجعة15focused tests لكل إصدار،309blobs مطابقة؛ CI قبل الدمج وبعده PASS عندmain9b7fa4e2. الموافقة الصريحة تخص#89 فقط، والسلطة التشغيلية غير متحققة.
