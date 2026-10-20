# إعداد مقارنة V1/V2 — T15

الحالة: **DRAFT_NOT_EXECUTABLE**. لا تشغيل نموذج أو ميزانية معتمدة أو نتيجة
مقارنة. `v1-v2-pilot.json` يحتوي 12 مقترحًا من اختبارات فعلية في المشروعين،
مع commit وGit blob لكل مرجع. طوبقت bytes المراجع عند إعداد المقترحات؛
لم تُشغّل اختبارات المشروعين ولم تُعدّل مصادرهما.

هذه المراجع عقود عامة سبق نشرها، وليست hidden acceptance. أوصاف mutations
مقترحات لإعداد fixtures لاحقًا، ولا تعني وجود العيوب في المصدر الحالي.
لم تُجهز fixture/prompt/hidden acceptance packages؛ قيم hashes الخاصة بها
`null` عمدًا. لا يجوز عرض المقترحات بوصفها dataset تشغيل مكتملة.

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
