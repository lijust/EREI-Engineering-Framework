# إعداد مقارنة V1/V2 — T15

الحالة: **DRAFT_NOT_EXECUTABLE**. لا تشغيل نموذج أو ميزانية معتمدة أو نتيجة
مقارنة. `v1-v2-pilot.json` يحتوي 12 مقترحًا من اختبارات فعلية في المشروعين،
مع commit وGit blob لكل مرجع. أُعدت ست وصفات معايرة عامة، وشُغّلت اختبارات
مصادرها المثبتة في نسخ مؤقتة. لم تُعدّل مصادر المشروعين أو بياناتهما.

هذه المراجع عقود عامة سبق نشرها، وليست hidden acceptance. mutations عيوب
محَقونة في نسخ المعايرة، ولا تعني وجودها في المصدر الحالي. ست مهام ما زالت
مقترحات؛ جميع `hidden_acceptance_sha256` تبقى `null`. لا يجوز عرض إعداد
المعايرة بوصفه dataset مقارنة مكتملة أو دليل تفوق V2.

## أصغر جزء تنفيذي

`evals/benchmark_accounting.py` يحسب جدولًا وحسابات محلية من JSON؛ لا يشغّل
وكيلًا أو نموذجًا أو shell أو شبكة، ولا يكتب ملفات. لا توجد خدمة أو قاعدة
بيانات أو LLM judge جديدة. يستخدم الاختبار الحقيقي لاحقًا runtime موجودًا
بعد مراجعته؛ هذه الأداة لا تستبدل adapter أو Evaluation Harness.

```text
python -B evals/benchmark_accounting.py --plan evals/benchmarks/v1-v2-pilot.json
python -B evals/benchmark_accounting.py --plan evals/benchmarks/v1-v2-pilot.json --records <records.json>
python -B -m unittest discover -s evals/tests -p test_benchmark_accounting.py -v
```

بدون records ينتج 48 slot: 12 مهمة × V1/V2 × تكرارين. يتبدل ترتيب الذراعين
بين التكرارين لكل مهمة، وترتب أزواج التنفيذ بـSHA-256 مع seed مثبت قبل جمع
النتائج. هذا deterministic allocation، وليس blind transport؛ الجدول يتضمن
arm labels ويخص منسق الدراسة، ولا يُرسل كما هو إلى المراجع الأعمى.

الأداة تتحقق من accounting structure، ولا تتحقق من صلاحية إعداد runtime
أو اكتمال dataset أو أذونات الإنفاق. يبقى `execution_authorized=false`
دائمًا، حتى عند تقديم سجل كامل.

## عقد records

الملف object بالمفاتيح الثلاثة التالية فقط:

- `plan_sha256`: قيمة مخرج الأداة للخطة كاملة. أي تغيير للخطة يغيّر الربط.
- `evidence_kind`: `synthetic` أو `observed_unverified`؛ يستخدم
  `no_observations` فقط مع قائمة فارغة.
- `runs`: سجلات slots المنفذة. عدم وجود slot يظهر صراحة في
  `missing_run_ids`، ولا يحذف من مقام الذراع البالغ 24.

كل run يحتوي فقط:

| الحقل | العقد |
|---|---|
| `run_id` | من الجدول؛ لا تكرار أو ID جديد غير مسند |
| `status` | `started/completed/failed/timeout/blocked/canceled` |
| `first_candidate_passed` | boolean أو `null` لتقييم أول candidate كامل وفق acceptance المثبتة |
| `independent_completion_passed` | boolean أو `null` لنتيجة القبول المستقل المعلنة |
| `review_evidence` | قائمة مراجع غير فارغة عند وجود assessment |
| `attempts` | محاولة واحدة على الأقل لكل run مرصود؛ جميع retries بالترتيب |

كل attempt يحتوي `attempt_no` متسلسلًا من 1 و`evidence_ref` غير فارغ،
و`wall_seconds/model_usd/tools_usd/ci_usd/human_usd`. كل قياس رقم finite
غير سالب أو `null`. تُرفض bool كرقم وNaN/Infinity والمفاتيح المكررة
والحقول غير المتوقعة. يجب تسجيل startup failure أو توقف بيئي كمحاولة
بالحالة المناسبة، حتى لو لم يُستدع نموذج؛ قيم التكلفة تُقاس ولا تفترض صفرًا.

تكلفة الإنسان هي القيمة المحوّلة إلى USD وفق معدل مثبت قبل التجربة. يجب
تخصيص كلفة الإعداد والمراجعة المشتركة وفق قاعدة معلنة واحدة للذراعين،
واستخدام مرجع سعر صرف مؤرخ إن احتاج التحويل. لا تُقدّر الأداة الأسعار.
`wall_seconds` للمحاولة تشمل وقتها المنقضي حسب تعريف موحد، وليست
runner-seconds. لا يستنتج مجموعها زمن نهاية إلى نهاية مع أعمال متوازية.

النص `independent` يصف assessment المعلن فقط؛ لا تصادق الأداة على هوية
المراجع أو الأدلة أو completeness الفعلي لعدد attempts.

## المقامات والقيود المضادة لإخفاء الفشل

- مقام النجاح هو جميع slots المسندة لكل ذراع، ويشمل timeout وblocked
  وcanceled. لا تستبعد حالة بعد رؤية النتيجة.
- `rate=null` ما دامت assessments ناقصة؛ تُعرض successes وcoverage
  وحدود missing data من `successes/assigned` إلى
  `(successes+unknown)/assigned`. هذه ليست confidence intervals.
- تضم التكلفة جميع attempts، بما فيها الإعادة والفشل. يظهر subtotal
  المقاس مع coverage؛ لا يتحول المكوّن المفقود إلى zero.
- لا تظهر total cost قبل انتهاء جميع slots واكتمال مكونات تكلفة كل attempt.
  ولا تظهر cost per declared verified run قبل اكتمال تقييم القبول أيضًا؛
  المقام صفر يعطي `null`.
- إذا قال السجل first-candidate success مع عدم قبول الإنجاز، أو completion
  ناجحًا مع terminal failure، يرفض الحساب التناقض.
- لا يمنع JSON caller كاذبًا من حذف attempt وإعادة ترقيم الباقي أو اختلاق
  reference أو تكلفة. يجب مطابقة trace المصدر بواسطة مراجع مستقل. hash
  الخطة ربط محتوى، وليس توقيع سلطة أو إثبات تنفيذ.
- المخرجات تبقى `comparability=NOT_VERIFIED` و
  `evidence_authenticity=NOT_VERIFIED` و`effectiveness=NOT_ESTABLISHED`.

## معايرة ست مهام من المصدر الفعلي

`calibration-packages.json` يربط كل prompt بالمصدر والاختبار وmutation واحدة
وGit blobs لجميع الملفات المطلوبة. لا ينسخ كود المشروعين داخل Framework.
`fixture_sha256` في الخطة هو SHA-256 للـJSON compact ذي المفاتيح المرتبة
أبجديًا لخريطة `starter_file_sha256`؛ كل قيمة فيها hash لبايتات ملف starter.
`prompt_sha256` يخص UTF-8 للنص دون newline إضافية. هذه روابط محتوى وليست
إثبات قبول مستقل.

| المهمة | العيب المحقون | دليل المعايرة المحلي |
|---|---|---|
| APP-01 | كتابة/style غير ضروريين عند تطابق headers | سكربت fake sheet الأصلي |
| APP-02 | مقارنة spelling بدل القيمة الرقمية | سكربت consensus الأصلي |
| APP-06 | إعادة snapshot عند اختلاف السياق | سكربت fake repository الأصلي |
| PY-02 | إدخال failed attempt في reusable cache | 4 دوال اختبار أصلية |
| PY-04 | إسقاط آخر token من full preset | 6 دوال اختبار أصلية |
| PY-05 | ترك connection دون close | 6 دوال اختبار أصلية |

الكود الأصلي ينجح والـstarter يفشل في assertion متوقع لكل مهمة. هذا اختبار
صلاحية للمعايرة، وليس محاولة حل أجراها نموذج. المهام صغيرة ومتعمدة العيب،
وقد يسهل عكس mutation؛ لا تمثل وحدها تطوير ميزات أو productivity فعلية.
الاختبارات العامة لا تغطي كل قبول لاحق: مثل cleanup عند فشل قراءة DB
في PY-05، أو أنواع context إضافية في APP-06.

لإعادة الإنتاج، جهّز exports محلية موثوقة من المصدرين المثبتين في الخطة:
`app/` لـApp Google و`py/` لـEREI-3.2، مع الحفاظ على مسارات الملفات والبايتات.
يكفي توفير الملفات المدرجة في `files` لكل وصفة. لا تستخدم working tree
متغيرًا أو تنزيلًا غير مثبت. الأداة لا تنزل ملفات ولا تثبت تبعيات.

```text
python -B evals/benchmarks/check_calibration.py --source-exports <exports-directory> --node <absolute-node-executable>
python -B evals/benchmarks/check_calibration.py --source-exports <exports-directory> --task PY-02
python -B -m unittest discover -s evals/tests -p test_calibration_packages.py -v
```

الأداة opt-in وخارج تشغيل CI المعتاد. تتحقق أولًا من جميع Git blobs المختارة،
ثم تستخدم البايتات نفسها لإنشاء reference وstarter منفصلين في temp directories.
لا تعدّل الاختبارات ولا export الإدخال. تعمل Python بـ`-I -S -B` دون
site packages؛ تُستدعى دوال الاختبار المثبتة عبر `unittest` مع دعم `tmp_path`
فقط. لا تدّعي هذه الطريقة تشغيل pytest أو conftest أو كامل اختبارات المستهلك.
تعمل سكربتات Node الأصلية مباشرة. المصدر المقروء راجعه مؤلف الإعداد قبل
التنفيذ؛ الأداة ليست sandbox لتشغيل كود وكيل غير موثوق.

لا يُحسب timeout أو import/syntax error أو عدم جمع الاختبارات ككشف ناجح
للعيب. المخرجات تشمل الأصل والنسخة المحقونة وتبقى
`PUBLIC_CALIBRATION_ONLY / independent_review=NOT_PERFORMED`.
لا تشغّل الأداة نموذجًا أو provider أو خدمة إنتاج؛ SQLite هنا in-memory/temp.
يجب مراجعة أي وصفة جديدة أو dependency قبل توسيع هذا المسار.

المقترحات المتبقية تحتاج عملًا حقيقيًا قبل تجميد dataset:

- APP-03: إعداد كامل dependencies وmutation سلوكية لحدود provenance.
- APP-04: استكمال assertion سلوكية لتخصيص ID؛ الاختبار الحالي يفحص نص
  المصدر والسياسات أساسًا، ويمكن أن يمر مع معادلة خاطئة إذا بقي النص المتوقع.
- APP-05: فصل قبول refactor السلوكي عن شرط builder المثبت لـsource blob؛
  لا تجعل تجاوز فحص الهوية حلًا مقبولًا للمهمة.
- PY-01/PY-06: تجميد dependency environment لـ`jsonschema` والمكونات
  المستوردة، مع FakeProvider فقط؛ التبعية غير متاحة في Python المحلي الحالي.
- PY-03: حصر سلسلة extractor imports وHTML dependencies قبل تنفيذها؛
  لا تحوّل اختبار parser إلى تشغيل extraction أو شبكة.

عدم اكتمال هذه الست لا يغير مقام الخطة إلى ست مهام ولا يسمح بحذف slots بعد
النتائج. أي تغيير لاحق في dataset يتطلب خطة جديدة مثبتة قبل جمع المقارنة.
قبل إرسال starter لوكيل، يفصل المنسق recipe/reference/mutation metadata
عن workspace المهمة؛ الملف الحالي علني ولا يوفر blinding تلقائيًا.

## استكمال التجربة قبل طلب اعتماد التكلفة

1. قبول T05/T13/T14 وتثبيت V2 commit/tree واحد. اختيار 12 fixture فعلية
   قابلة للحل ومتماثلة بين الذراعين، مع prompt وpackage hashes. التحقق
   مستقلًا من أن mutations تخلق المشكلة المطلوبة ولا تجعل المهمة مستحيلة.
2. استخدام العقود العامة الحالية للمعايرة فقط. يعدّ مراجع مستقل variants
   جديدة وacceptance خارج workspace المرئي للوكيل؛ لا يوصف اختبار منشور
   بأنه مخفي. تثبيت قواعد التقييم وحالات النقص والأمن قبل النتائج.
3. تثبيت model/revision وruntime وOS/dependencies وpermissions وtime/token
   caps ونفس project SHA لكل زوج. الفرق المقصود Framework فقط؛ تبدأ كل
   محاولة في نسخة نظيفة بلا cross-arm memory/cache أو نقل حل من ذراع لآخر.
   أي سلوك L2 يُختبر على fake resources؛ لا credentials أو live calls.
4. تثبيت التاريخ التعلمي الصحيح نفسه للذراعين، وترك Learning Operations
   Candidate معطلة في مقارنة Core. اختبار أثر تدخل تعلم واحد يكون تجربة
   لاحقة منفصلة تربط adoption/exposure/outcomes بعقد #93.
5. تسجيل كل candidate وretry وtimeout والتدخل البشري والqueue/tool/model
   costs. فصل healthy iteration عن defect-driven rework بأسباب مقيمة،
   وعدم تسمية rework أو verification failure «دقة تنفيذ».
6. إعداد reviewer package يخفي arm labels ومراجع الإصدار قدر الإمكان،
   مع تسجيل حالات انكشاف الذراع. لا ادعاء blinding كامل لمجرد تبديل IDs.
7. مراجعة runtime ومصدر executable والميزانية القصوى وشروط التوقف، ثم
   الحصول على موافقة مستقلة على التشغيل المدفوع. لا يوجد تفويض هنا.
8. تحليل فروق الأزواج على مستوى task، مع التجميع عبر التكرارين؛ لا تعامل
   48 تشغيلًا كـ48 مهمة مستقلة. pilot لتقدير التباين وجدوى المنهج، وليس
   إثبات تفوق إحصائي مضمون. يثبت reviewer منهج uncertainty مسبقًا؛ لا
   تحسب هذه الأداة confidence intervals أو causal learning effects.

المقاييس الأوسع، مثل escape خلال نافذة متابعة، وroot-cause recurrence،
وreview debt، تحتاج سجلات exposure ومتابعة مستقلة؛ لا تُشتق من JSON
الإنجاز وحده. لا تقارن وقت الاختبار المحلي أو mock costs بإنتاج حقيقي.

## القبول والرجوع

قبول إعداد الأداة يحتاج اختبارات denominator/missingness/cost/retry
ومراجعة مستقلة. تبقى T15 `BLOCKED` للتنفيذ رغم نشر إعدادها.
يمكن التراجع عن هذا الإعداد دون تعديل بيانات أو pin؛ تحفظ سجلات أي
تجربة لاحقة ونتائجها بما فيها الإخفاقات، ولا تعاد كتابة الخطة لتناسبها.

## سجل التحقق المحلي المثبت

أُجريت معايرة 2026-10-20 على Windows، باستخدام Python 3.11.9 و3.12.10
وNode 24.20.0. [الأوامر والنتائج وهويات المصدر](https://github.com/lijust/EREI-Engineering-Framework/blob/4a47642ba933c04a45660c5e9b89934c72a71d23/governance/v2-remediation/evidence/verification-calibration-20261020.json)
محفوظة خارج working copies المؤقتة. اختبارات الكود تخص الرأس
`cf6fd76635f4417137b2babc5e1fc28a7291b95a`؛ إضافة رابط هذا السجل تغيير توثيقي فقط.

| الفئة | النتيجة على كل إصدار Python |
|---|---|
| accounting + checker unit tests | 27/27 PASS |
| المراجع الأصلية | 3 Node scripts +16 Python functions PASS |
| العيوب المحقونة | كشف 6/6 بواسطة assertions متوقعة |
| AI runs | 0 |

طابقت 314 Git blobs النسخة المختبرة؛ بقيت 13 input blobs من المشروعين دون
تغيير. هذه أعداد من فئات مختلفة؛ لا تُجمع كمهام نموذج مستقلة. CI والمراجعة
المستقلة بوابتان منفصلتان، ولا يمنح هذا السجل سلطة إصدار أو إثبات تفوق V2.

## تصحيح ربط assertion — 2026-10-21

كان فحص Node في APP-01 وAPP-02 يقبل ERR_ASSERTION عامًا دون ربطه بموضع
الفشل المتوقع. أثبت اختبار رجعي قبول ملف أو سطر مختلف، وكذلك ذكر موضع
الاختبار في رسالة بلا stack frame. صار الكشف يشترط test_path والسطر
expected_assertion_line داخل frame فعلية، مع تطبيع فواصل Windows/POSIX.
تُثبت الأسطر الثلاثة مع Git blobs الأصلية؛ أي تغيير في test blob يحتاج
إعادة معايرة موضعه. هذا ربط للمعايرة المثبتة، وليس مصادقة لمخرجات كود عدائي.

اجتاز التصحيح 28 unit tests على Python 3.11 و3.12؛ نجحت المراجع الست
وكُشفت mutants الست في المواضع المقصودة، وبقيت 13 input blobs دون تغيير.
دليل CI للرأس e10d3c345062d166c4447ed7ca7131470bcc1448 يخص ما قبل هذا
التصحيح؛ يلزم CI ومراجعة على الرأس الجديد. لا يتغير plan digest أو fixtures
أو prompts أو عدد AI runs (صفر). تبقى المراجعة المستقلة الكاملة غير مكتملة.
