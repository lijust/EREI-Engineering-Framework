# إعداد مقارنة V1/V2 — T15

الحالة: **DRAFT_NOT_EXECUTABLE**. لا تشغيل نموذج أو ميزانية معتمدة أو نتيجة
مقارنة. `v1-v2-pilot.json` يحتوي 12 مقترحًا من اختبارات فعلية في المشروعين،
مع commit وGit blob لكل مرجع. أُعدت **12/12 وصفة معايرة عامة من حيث المصدر والمراجع والـhashes**،
لكن **ليس 12/12 اختبار معايرة مكتملًا**: سبع وصفات لها أدلة معايرة سابقة؛
APP-04/APP-05 لهما Node VM oracle جديدة، وPY-03 لها AST oracle محدودة،
وPY-01/PY-06 تتطلبان اختبار ملفات المستهلك الأصلية ببيئة dependencies مضبوطة.
لا يتضمن هذا نجاح benchmark أو إثبات قبول مستقل؛ لم تُعدّل مصادر المشروعين أو بياناتهما.

هذه المراجع عقود عامة سبق نشرها، وليست hidden acceptance. mutations عيوب
محَقونة في نسخ المعايرة، ولا تعني وجودها في المصدر الحالي. كل المهام الـ12
مرتبطة الآن بوصفات **عامة فقط**؛ جميع `hidden_acceptance_sha256` تبقى `null`. لا يجوز عرض إعداد
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

## اثنتا عشرة وصفة معايرة عامة مثبتة بالمصدر

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
| APP-03 | نسخ master developer ID إلى external source identity | سكربت provenance الأصلي، مع بقاء write blockers |
| APP-04 | تغيير next candidate من أعلى ID + 1 إلى أدنى ID + 1 | فحص Node VM سلوكي إضافي من Framework، يقرأ دالة المصدر الأصلية ويدخل IDs 2/5، ولا يشغل السكربت الأصلي النصي كاختبار قبول |
| APP-05 | كسر cache داخل مصدر generator الخاص بـErrorCatalogRepository | فحص Node VM سلوكي إضافي من Framework يقارن كود ورسائل وأكواد HTTP وسلوك تحميل المزوّد مرة واحدة مع المصدر القديم، وليس تشغيل test الـbuilder النصي الأصلي |
| APP-06 | إعادة snapshot عند اختلاف السياق | سكربت fake repository الأصلي |
| PY-01 | تحويل فشل FakeProvider إلى NORMALIZED زائف | 20 دالة من اختبار المستهلك الأصلي؛ تتطلب بيئة jsonschema مطابقة للإصدارات المثبتة، ولم تُنفذ end-to-end بعد |
| PY-02 | إدخال failed attempt في reusable cache | 4 دوال اختبار أصلية |
| PY-03 | استبدال حدود marker المطابقة بدقة بمطابقة substring | oracle عامة محدودة تشغّل AST من method Nawy الأصلية على نصوص EN/AR، دون شبكة أو HTML parser كامل |
| PY-04 | إسقاط آخر token من full preset | 6 دوال اختبار أصلية |
| PY-05 | ترك connection دون close | 6 دوال اختبار أصلية |
| PY-06 | تمرير installment_months رقمية غير مستندة لنص المصدر | 4 دوال أصلية بأدلة words/derived arithmetic وسلسلة 9 ملفات core.ai مثبتة؛ تحتاج exact local dependency versions |

في المعايرات السبع السابقة ينجح الكود الأصلي ويفشل الـstarter عند assertion
متوقعة؛ وصفتا APP-04 وAPP-05 أُعدتا اعتمادًا على oracle سلوكية جديدة للـVM
وتحتاجان إعادة تحقق مستقلة من تنفيذ Node على نسخ المصدر المثبتة بالكامل.
PY-03 تستخدم oracle عامة تقطع dependencies بالـAST؛ لا تختبر parser الكامل. هذا إعداد
معايرة عامة، وليس محاولة حل أجراها نموذج. المهام صغيرة ومتعمدة العيب،
وقد يسهل عكس mutation؛ لا تمثل وحدها تطوير ميزات أو productivity فعلية.
الاختبارات العامة لا تغطي كل قبول لاحق: مثل cleanup عند فشل قراءة DB
في PY-05، أو أنواع context إضافية في APP-06.

لإعادة الإنتاج، جهّز exports محلية موثوقة من المصدرين المثبتين في الخطة:
`app/` لـApp Google و`py/` لـEREI-3.2، مع الحفاظ على مسارات الملفات والبايتات.
يكفي توفير الملفات المدرجة في `files` لكل وصفة. لا تستخدم working tree
متغيرًا أو تنزيلًا غير مثبت. **مستودعا EREI-3.2 وEREI-App-Google خاصان،
ومستودع Framework عام**: يجب إبقاء نسخ المصادر الخاصة **خارج مجلد Git
العام**. يرفض checker أي `--source-exports` داخل Framework checkout بعد
حل المسار الحقيقي (حتى لو مجلدًا فرعيًا موجودًا بالفعل). لا تضف تلك النسخ
إلى Git أو artifacts أو سجلات GitHub Actions العامة؛ نفّذ المطابقة في بيئة
خاصة مخوّلة وموثوقة فقط. الأداة لا تنزل ملفات ولا تثبت تبعيات.

```text
python -B evals/benchmarks/check_calibration.py --source-exports <exports-directory> --node <absolute-node-executable>
python -B evals/benchmarks/check_calibration.py --source-exports <exports-directory> --task PY-02
python -B -m unittest discover -s evals/tests -p test_calibration_packages.py -v
```

الأداة opt-in وخارج تشغيل CI المعتاد. تتحقق أولًا من جميع Git blobs المختارة،
ثم تستخدم البايتات نفسها لإنشاء reference وstarter منفصلين في temp directories.
لا تعدّل الاختبارات ولا export الإدخال. وصفات Python الافتراضية تعمل بـ
`-I -S -B` دون site packages؛ **PY-01/PY-06 فقط** تعمل opt-in بـ`-I -B`
مع إتاحة local site packages واشتراط تطابق إصدارات dependencies المثبتة
في `dependency_versions` حرفيًا؛ أي نقص أو اختلاف في الإصدارات يوقف الاختبار
دون اعتماد نتيجة. لا ترفع الأداة dependencies أو تحملها من الشبكة. تُستدعى
دوال الاختبار المثبتة عبر `unittest` مع دعم `tmp_path` فقط. لا تدّعي هذه الطريقة تشغيل pytest أو conftest أو كامل اختبارات المستهلك.
تعمل سكربتات Node الأصلية مباشرة في الوصفات السبع السابقة؛ APP-04 يستعمل
oracle إضافية عامة مُضمّنة في checker لاستدعاء inventory function من مصدر
Apps Script الحقيقي بـmock read-only (ID 2 و5، فجوات 3 و4، النتيجة 6)،
وAPP-05 يستدعي `candidateErrorServiceSource()` من builder المثبت دون تشغيل
`buildCandidate()` أو تجاوز git blob، ويقارن provider-read/cache/parity
في VM ببيانات مزوّد زائفة. لا توجد Google API أو تعديلات للاختبارات الأصلية. oracle عامة **ليست** الاختبار الأصلي
ولا تعد acceptance خفية. المصدر المقروء راجعه مؤلف الإعداد قبل
التنفيذ؛ الأداة ليست sandbox لتشغيل كود وكيل غير موثوق.

لا يُحسب timeout أو import/syntax error أو عدم جمع الاختبارات ككشف ناجح
للعيب. في وصفات Python، يجب أن يفشل **اختبار واحد محدد فقط** من الاختبارات
المثبتة؛ فشل الاختبار المطلوب مع اختبارات أخرى لا يُحسب معايرة ناجحة، حتى لو
كان الـmutant يثير assertion المتوقعة. المخرجات تشمل الأصل والنسخة المحقونة وتبقى
`PUBLIC_CALIBRATION_ONLY / independent_review=NOT_PERFORMED`.
يحجب التقرير العام الآن النصوص الخام لـstdout/stderr ورسائل الفشل وأسماء الاختبارات
الفاشلة والـtraceback، ويعرض فقط return codes، وعدّادات الاختبارات،
وبصمات SHA-256 للمخرجات للمقارنة. لا تحفظ التقرير المُنقّى بوصفه سجلًا
تفصيليًا كافيًا للتحكيم المستقل: يجري فحص الفشل من المخرجات الخام في
الذاكرة داخل بيئة المصدر الخاصة ثم يُصدر تقريرًا منقحًا؛ أي أدلة تشخيصية
أصلية تبقى في بيئة خاصة مصرح بها ولا تُرسل إلى GitHub Actions العام.
لا تشغّل الأداة نموذجًا أو provider أو خدمة إنتاج؛ SQLite هنا in-memory/temp.
يجب مراجعة أي وصفة جديدة أو dependency قبل توسيع هذا المسار.

الوصفات الـ12 الآن محددة بالمصدر، لكن **قبولها النهائي يحتاج عملًا حقيقيًا**:
إعادة تشغيل baseline/mutant من exported source بالـGit blobs المثبتة، ومنها
`PY-01/PY-06` داخل بيئة Python محلية موثوقة ذات إصدارات dependencies المحددة
والموجودة سابقًا، ثم مراجعة مستقلة على الهوية والـfailures. هذا ليس تصريحًا
بتثبيت تبعيات من الشبكة أو بدء LLM benchmark. اكتمال تجهيز الـ12 لا يسمح بحذف
أي slot بعد النتائج. أي تغيير لاحق في dataset يتطلب خطة جديدة مثبتة قبل جمع المقارنة.
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
أو prompts أو عدد AI runs (صفر). اكتملت المراجعة المستقلة الكاملة لإعداد المصدر عند
`da9b5160d8fc9789fb878683b24d3f287e759483`؛ توسعات dataset اللاحقة
تحتاج مراجعتها وأدلتها الخاصة.

## إضافة APP-03 — 2026-10-21

تضم الوصفة سبعة source/test/contract blobs مثبتة من App Google.
تُحقن هوية master developer في الحقل الخارجي source_developer_id، بينما
الاختبار الأصلي يشترط بقاءه فارغًا لمقترح DVI-origin. يكتشف assertion
في السطر 59 هذه الهوية الخاطئة؛ يفحص المرجع أيضًا بقاء حقلي provenance
فارغين وwrite authorization وaudit-linkage blockers وعدم حجز project ID.
لا تُنقل أرقام الأدلة التاريخية في ملفات العقود إلى بيانات live جديدة.

هذا يجهز 7/12 وصفة للمعايرة العامة، مع بقاء 5 مقترحات وhidden acceptance
غير مكتملة. تغير plan digest بسبب إضافة fixture/prompt، قبل أي AI run.
تظل snapshots ذات ست وصفات وdigest السابق محفوظة. تمت مزامنة ملفي
اختبارات quoting من main64f9d97230f95d4e663369b6d4a54e941964effa
الذي دمج #85، كي يتبع فرع الإعداد المصدر المعتمد.

## إضافة APP-04 — 2026-10-24 (مصدر جاهز، معايرة Node شاملة لم تُثبت بعد)

أُضيفت وصفة عامة ثامنة للمهمة `APP-04`؛ اختبارات App Google الأصلية
`developer-validation-project-id-policy.test.js` تتحقق من نص السياسة ولا
تشغّل دالة `dviMissingProjectInsertMasterInventory_` سلوكيًا. لهذا لم يُحسب
نص السياسة وحده oracle كافية. تَستخدم الوصفة source blob المثبت عند commit
`6d32e7a14a4324dbdea228f695d6b75e0b8bd246` مع اختبار المستهلك
المثبت (read-only ولم يُعدّل)، وتُنفّذ oracle جديدة صريحة من Framework
عبر Node VM في نسخة مؤقتة: Master IDs = `[2,5]`، الفجوات `3,4`،
`nextCandidate=6`. mutation محكومة تستبدل **موضع الإسناد الوحيد**
`? projectIdMax+1 : null` بـ`? projectIdMin+1 : null`، مع إبقاء
فحص overflow كما هو. ظهر فرق السلوك 6 مقابل 3 في الفحص المباشر لمصدر
GitHub المثبت، ولم تحدث أي عملية حجز/تخصيص ID أو كتابة Master.

الوصفة **PUBLIC_CALIBRATION_ONLY** ويجب تشغيلها على exports المصدر الحقيقية
بالـchecker وتوثيق baseline/mutant قبل اعتبارها `CALIBRATION_PASS`.
لا تُعتبر test النصية الأصلية اختبارًا سلوكيًا. كانت **8/12 وصفات مجهزة
عند إضافتها**؛ بعد إضافة APP-05 أصبح الإجمالي **9/12 مجهزة**، وبقيت
PY-01 وPY-03 وPY-06 غير مجهزة، مع بقاء 48 slot، وصفر تنفيذ مقارنة V1/V2 ممولة، وغياب
hidden acceptance والتفويض والتقييم المستقل.

## إضافة APP-05 — 2026-10-24 (وصفة عامة جاهزة، تحتاج تحقق consumer exports)

الوصفة التاسعة تثبت **ثلاثة blobs** من App Google عند commit
`6d32e7a14a4324dbdea228f695d6b75e0b8bd246`: مصدر
`src/11_ErrorService.gs`، و`tools/build-error-catalog-repository-candidate.js`،
واختبار `tests/error-catalog-repository-candidate.test.js` غير المُعدّل.
لا يجري checker استدعاء `buildCandidate()` الذي يفترض Git HEAD ومجلد
`src` كاملًا؛ بل يستدعي الدالة الأصلية الموثقة
`candidateErrorServiceSource()` في Node VM من البايتات المثبتة، ثم
يفحص فصل وصول المزوّد عن ErrorService، ومطابقة خمسة vectors للأكواد
والرسائل والتفاصيل وHTTP، ومطابقة عدد القراءات السابق (واحدة).
الطفرة الوحيدة تُعطّل حارس `if (cache_) return cache_;` داخل نص
الـbuilder المثبت، لتعيد قراءات المزوّد رغم توافق المخرجات. تمت تجربة
الباني المثبت في JS isolate: المرجع provider reads = 1/1 مقابل mutant = 7/7.
الفحص السلوكي الإضافي **عام وFramework-owned**، وليس اختبار المستهلك
الأصلي أو hidden acceptance. لم تُعتمد نسخة تطبيق أو كتابة مصدر أو نشر.

**الحالة المحاسبية:** **9/12** وصفات مُجهزة بالـpins والـhashes؛ تبقى
`PY-01` و`PY-03` و`PY-06` غير مجهزة، ولا تُرفع APP-05 إلى
`CALIBRATION_PASS` قبل تشغيل checker على export المصدر المثبت
وتوثيق baseline/mutant/المراجعة. تظل 48 مقارنة مخططة، 0 model
observations، `DRAFT_NOT_EXECUTABLE` و`effectiveness=NOT_ESTABLISHED`.

## إضافة PY-03 — 2026-10-24 (الوصفة العاشرة العامة، parser stack ليس ضمنها)

ثُبت source blob `6f165f875aa3aec8db8b2d2ff26eedfa904bd473` الخاص بـ
`extractors/nawy/payment_section_boundary_extractor.py` وblob الاختبار
الأصلي `2a1353992f626bdf9d8b58db9a0d18f3c15be4c6` من
`lijust/EREI-3.2@87d730ddc3547f863de2a6895e91f9b83e9c6e72`.
تُحقن طفرة substring وحيدة بدل exact matching عند شرط
`if cls._normalized_boundary_text(line) in stops:`. اختبار Framework
الجديد يستخدم `ast.parse` ثم يحمّل class `NawyExtractor` المثبتة
من source الأصلي كما هي داخل Python `-I -S -B`، مع fake
`_PaymentNawyExtractor._clean_text` لتطبيع أسطر **نصية صريحة فقط**.
ثلاث assertions عامة: فاصل EN الصحيح، فاصل AR الصحيح، والاحتفاظ بجملة
تشبه `Location on Map` لكن ليست marker كاملة؛ الأخيرة وحدها تفشل
مع mutation. **لا يتم** تشغيل HTML parser أو `extractors.nawy` الكامل،
ولا pytest أو network. اختبار المستهلك الأصلي مرفق بباطن blob ثابت لكنه
**غير منفذ في الوصفة**؛ لا تعرض نتيجة oracle كتكافؤ كامل مع extractor.

بعد إضافة PY-03، **10/12 وصفات مجهزة بالمصدر والـhashes**، ويبقى
`PY-01` و`PY-06` يحتاجان dependency-resolved `jsonschema`
وإغلاق سلسلة imports قبل تجميد وصفات فعلية؛ لا تُزال هذه المهام من
الـ48 مقارنة المخططة، ولا يُسمح بتنفيذ نموذجي مدفوع أو إصدار Stable
على أساس هذه التحضيرات. معايرة PY-03 الكاملة بالـchecker وexports
المثبتة وتقييم مستقل لا تزال مطلوبة.

## إكمال Source Recipes PY-01 + PY-06 — 2026-10-24

- **PY-01**: ثبت المصدران `payment_plan_normalizer.py` و`provider.py` واختبار
  `test_payment_plan_semantic_normalizer.py` الأصلي (20 وظيفة اختبار)
  عند `lijust/EREI-3.2@87d730dd...`. Mutation وحيدة في `except AIProviderError`
  تستبدل `PROVIDER_ERROR` بـ`NORMALIZED` بصورة زائفة، ويجب أن تفشل
  `test_provider_failure_does_not_destroy_raw_evidence` فقط عند تشغيل المصدر.
- **PY-06**: ثبت جميع ملفات `core.ai` التسعة المطلوبة بسلسلة
  `semantic_domains → semantic_{address,facilities,harvest,project_intelligence,unit_types}`
  بالإضافة إلى cache/normalizer/provider، واختبار number-word الأصلي
  (4 وظائف). Mutation تسمح بـ`installment_months` غير المستندة لدليل؛
  يجب أن يفشل اختبار derived eight-years-to-96-months فقط.
- **Environment pin**: `jsonschema=4.26.0`, `attrs=26.1.0`,
  `referencing=0.37.0`, `rpds-py=2026.5.1`,
  `jsonschema-specifications=2025.9.1`. نسخة Python الأصلية تُشغّل
  `-I -B` في venv محلية مجهزة مسبقًا بهذه الإصدارات؛ لا تستخدم `-S`
  للوصفات المعتمدة على jsonschema. أي mismatch يفشل قبل استدعاء الاختبار،
  وتظل بقية الوصفات في الوضع الصارم `-I -S -B`.

**معنى 12/12 هنا: ملفات recipe/prompt/fixture pin والتحقق من الصيغة مُجهزة،
لا يعني اكتمال معايرة المصدر فعليًا أو إجراء 48 مقارنة أو وجود hidden acceptance.**
تظل الحالة `DRAFT_NOT_EXECUTABLE`, `execution_authorized=false`,
`effectiveness=NOT_ESTABLISHED`, ولا تفويض بالصرف أو الدمج أو الإصدار.

## محضر تشغيل فعلي محدود على المصادر الأصلية — 2026-10-24

`public-source-oracle-observation.2026-10-24.json` يسجل **رصدًا ذاتيًا غير معتمد
من مراجع مستقل**: فحص 35/35 من Git blobs الحقيقية في مستودعين خاصين؛
12/12 تغييرًا واحدًا في موضعه مع بصمات الـstarter؛ وتشغيل methods الأصلية
`APP-04` و`APP-05` و`APP-06` على JS V8 ببيانات mock دون كتابة،
وتشغيل Python class من source الأصلي `PY-03`. في APP-06 اختُبرت حالات
snapshot السليمة، واختلاف subscriber أو workspace، وغياب person؛
كل حالة تستخدم قراءة repository واحدة، ونسخة الخطأ تتجاوز رفض
اختلاف السياق. هذا ليس تشغيل PostgreSQL حقيقي. **بالإضافة** إلى هذا oracle، شُغّل
`APP-06` لاحقًا من نسختي المصدر والاختبار الأصلي غير المعدّل بعد مطابقة
Git blob لكل منهما، في Node 22.16.0 بمجلد مؤقت خارج Git العام:
المرجع **PASS (exit 0)** والطفرة الوحيدة **FAIL (exit 1)** من
`tests/prd03-production-edge-context-resolver.test.js:57` بسبب
`Missing expected rejection`. هذا تشغيل كامل لملف الاختبار الأصلي
المحدد لـAPP-06 مع mock repository الخاص به، وليس اختبار اتصال PostgreSQL
أو محضر اعتماد مستقل. إضافة إلى الـ3 tests
العامة المحدودة في PY-03، جرى تشغيل **اختبار واحد أصلي غير معدّل من 3**
لـPY-03 (`test_boundary_matching_is_exact_not_substring_based`)،
حيث نجح baseline وفشل mutant كما هو متوقع، بعد فحص Git blobs لملفي
المصدر والاختبار داخل منطقة مؤقتة خارج Git Framework العام. احتاج هذا
التشغيل إلى import shim لواجهة extractor؛ لذلك **لم تُختبر دوال HTML
parser الأصلية في نفس التشغيل**. لا يتضمن الرصد نتائج المعايرة الكاملة
لمكونات Python المعتمدة على البيئة كاملة.

هذا محضر سلوكي محدود **ليس** تحققًا مستقلًا ولا hidden acceptance،
ولا يعني تشغيل 48 تجربة V1/V2 أو إغلاق T15. حافظ على خصوصية الملفات
الأصلية؛ لا تُلحق stdout/stderr خامًا بمحضر عام. CLI مصمم الآن لإخراج
بصمات ومجاميع منقحة، ويعطي رسالة `FAIL_CLOSED` دون المسارات أو
tracebacks الخام عند استثناء غير متوقع.

### معايرتان إضافيتان بالاختبارات الأصلية غير المعدلة — PY-02 / PY-05

نفذنا اختبارات المستهلك الأصلية من ملفات `EREI-3.2` المثبتة (Git blob
مطابق) خارج مستودع Framework العام، ببيئة Python `-I -S -B` دون
network أو خدمات إنتاج أو pytest plugins. تُستدعى الدوال الأصلية نفسها
عبر `runpy` و`unittest`، مع `tmp_path` مؤقت لاختبار PY-02:

- `PY-02`: المرجع **4/4 PASS / exit 0**. طفرة إدخال provider-error
  محاولة إلى reusable cache أعطت **3/4 PASS، 1 intended FAIL / exit 1**
  في `test_attempt_ledger_does_not_poison_reusable_result_cache`.
  استخدم SQLite داخل الذاكرة/المسار المؤقت فقط.
- `PY-05`: المرجع **6/6 PASS / exit 0**. طفرة تعطيل
  `conn.close()` أعطت **5/6 PASS، 1 intended FAIL / exit 1**
  في `test_load_unit_type_mapping_uses_short_lived_connection_and_normalizes_keys`.
  الاتصال كان `FakeConnection` وليس قاعدة تشغيل حقيقية.

بهذا لدينا محاضر تشغيل **ثلاثة ملفات اختبارات مستهلك أصلية كاملة
(APP-06، PY-02، PY-05)** بنجاح baseline وفشل mutant كما هو مقصود،
بالإضافة إلى اختبار واحد أصلي من ملف PY-03، وAPP-04/05 باستخدام
oracles عامة على methods المصدر الحقيقي. العدد ليس 12/12 من قبول
المستهلك، ولا يشمل مقارنة نموذجية أو hidden acceptance أو توقيع مراجع مستقل.

## تجهيز ملفات المعايرة الأصلية دون نقلها إلى المستودع العام

أُضيفت أداة `prepare_private_exports.py` لتسهيل تشغيل اختبارات المستهلك
الأصلية عبر GitHub CLI في **بيئة خاصة موثوقة فقط** لها صلاحية قراءة
المستودعين الخاصين. لا تغيّر الأداة المصدر الأصلي أو تنفذ كتابة إنتاجية:
تقرأ قائمة الملفات من `calibration-packages.json` العامة، وتطلب الملفات
من private GitHub Contents API عند commit SHA ثابت (ليس branch HEAD)،
ثم تتحقق من Git blob SHA-1 للبايتات الفعلية، وتنسخها إلى مجلد مؤقت خارج
Framework Git. بعد تحقق كل الملفات، تنقل المجلد إلى مسار خاص جديد.
أي فشل يمحو الملفات المؤقتة ويخرج رسالة عامة دون خطأ API أو محتويات خاصة.

أوامر الاستخدام على جهاز مصرح به ومجهز سابقًا بـ`gh` والـPython المناسب:

```text
python -B evals/benchmarks/prepare_private_exports.py --destination <absolute-private-new-directory> --task PY-04
python -B evals/benchmarks/check_calibration.py --source-exports <absolute-private-new-directory> --task PY-04
```

يمكن إغفال `--task` فقط عند تجهيز جميع الـ12 دفعة واحدة: 35 ملفًا فريدًا
من المستودعين الخاصين، ولا يُكرر سحب الملف الواحد. لا تستخدم مسارًا داخل
checkout العام أو موقعًا تلتقطه GitHub Actions artifacts/logs تلقائيًا.
يجب أن يكون `--destination` **مسارًا مطلقًا غير موجود مسبقًا** داخل
مجلد خاص موجود مسبقًا. لا تطبع الأداة بايتات المصدر أو أخطاء `gh` الخام.
الاختبارات العامة في CI تستخدم mock كاملًا لـ`gh`، ولا تطلب حق الوصول
إلى أي مستودع خاص ولا تنزل ملفات خاصة.

في Python consumer tests يتجاوز `check_calibration.py` ملفات
`core/__init__.py` و`core/ai/__init__.py` وباقي package initializers
الكبيرة باستعمال namespace-package محلية محددة؛ لتجنب تحميل desktop
وprovider/network الاختياري من نظام المشروع القديم. يتم تنفيذ modules
المثبتة والاختبارات الأصلية نفسها، **لكن لا يُعتبر هذا تشغيل التطبيق
الكامل أو pytest plugins**. PY-01/PY-06 تتطلبان الإصدارات المحلية
المحددة مسبقًا من `jsonschema` وdependencies؛ لا تثبت الأداة أي باكدج.
وتبقى معايرة APP-04/05 مقيّدة بالـoracles العامة الموثقة سابقًا.

**حدود الإثبات:** هذه أداة تحضير وتشغيل محلي opt-in وليست دليلًا أن
جميع معايرات المستهلك نجحت في بيئة المستخدم، وليست ترخيصًا لتشغيل
48 مقارنة V1/V2 أو الدمج/الإصدار دون مراجعة مستقلة.

### فحص APP-01 / APP-02 / APP-03 بالسورس والاختبارات الأصلية — JS V8 محدود

استُخدم GitHub connector المصرح له لقراءة بايتات المصدر والاختبار
من `EREI-App-Google@6d32e7a...` الخاصة، ثم نُفّذ **نص الاختبار
الأصلي كما هو** في V8 مع محاكاة محددة لـ `require('fs')`,
`require('path')`, `require('assert')`، و`vm.runInNewContext`
في APP-03. لم تُنسخ ملفات المستودع الخاص إلى Framework العام.

- `APP-01`: دالة `dviEnsure_` الأصلية نجحت في اختبار idempotent
  headers، ثم فشل assertion المقصود بعد تعديل
  `needsHeaderWrite=created` إلى `true`.
- `APP-02`: منطق `dviEvidenceFieldDecision_` و
  `dviConsensusValueKey_` الأصلي نجح، ثم فشل اختبار
  canonicalization الرقمي بعد تعديل `return String(n)` إلى
  `return raw`.
- `APP-03`: سياسة source developer provenance نجحت في الاختبار
  الأصلي، ثم فشل بالرسالة المتوقعة `source_developer_id must stay blank
  for DVI-origin` بعد حقن external ID من master.

هذه الاختبارات **تنفذ نصوص المستهلك الأصلية والمصدر الفعلي**، لكنها
ليست ملفات اختبار Native Node CLI كاملة، لأن واجهات Node وبعض
سلوك VM جاءت من mocks محدودة. لذلك لا تدخل هذه الثلاثة في عداد
ملفات اختبارات المستهلك الأصلية الثلاثة المنفذة بالكامل
سابقًا (APP-06، PY-02، PY-05). سجل النتائج يحفظ البصمات
والحالة فقط، والتصنيف ما زال `SELF_REPORTED_UNATTESTED_SOURCE_EXECUTION`.

بذلك هناك رصد سلوكي محدود لتسع مهام من أصل 12، وتبقى
`PY-01` و`PY-04` و`PY-06` بلا رصد تشغيل فعلي في هذا المحضر؛
لا يُحسب ذلك تقييم V1/V2 أو قبولًا مستقلًا أو تفويض إصدار.

### فجوة اختبار أصلية مكتشفة — APP-04 (لا تُحسب معايرة ناجحة)

اختُبر نص `tests/developer-validation-project-id-policy.test.js` الأصلي
بلا تعديل على مصدر `MissingProjectInsertReadiness.gs` المثبت، ثم مع
تغيير `projectIdMax+1` إلى `projectIdMin+1` في الموضع المحقون فقط.
كانت النتيجة **PASS للمرجع وPASS للطفرة** في فحص JS V8 الافتراضي:
الاختبار يعتمد على وجود نص `projectIdMax+1` في الملف عمومًا،
ويمكن أن يبقى النص في موضع آخر حتى لو تغيّرت دالة تخصيص المعرّفات.

هذه **False Negative / Mutation Survivor** ولا يجوز احتسابها نجاح
اختبار المستهلك. الـoracle السلوكي الإضافي الموثق في APP-04 هو
الذي اكتشف الاختلاف، باستخدام معرفَي مشروع 2 و5:
المرجع يقترح 6، والطفرة تقترح 3 (إعادة استخدام gap).
يلزم اختبار قبول مستقل يربط النتيجة الحسابية بالدالة المعتمدة؛
لا يكفي فحص وجود token نصي وحده.

لم تُنفذ في هذا الفحص عملية Google Sheets فعلية، ولا تُعد النتائج
اختبار Node الأصلي الكامل أو توقيع مراجع مستقل.
