# متطلبات المنظومة الهندسية الشاملة لوكلاء البرمجة — EREI / UER v0.1

**التاريخ:** 2026-11-13  
**الحالة:** `REQUIREMENTS_BASELINE_FOR_REVIEW` — وثيقة بحث/قرار، لا تفعيل Runtime ولا ترقية Framework.  
**الهدف الحقيقي:** توجيه أي AI coding agent مدعوم إلى تنفيذ وإنشاء وتعديل مشروع برمجي بجودة هندسية عالية **بقدر ما تثبته أدلة المشروع**، لا تدريب نموذج لغوي جديد.  
**القيد:** لا توجد منظومة تستطيع أن تضمن جودة *أي* برمجية دون فهم مجالها، أو قيود منصتها، أو اختبارها؛ التطبيقات عالية السلامة/التنظيم تحتاج متطلبات ومراجعين مختصين إضافيين.

## 1. تصحيح نقطة البداية

- قائمة [9 مجالات/180 مفهومًا](./web-engineering-9-domains-180-concepts-ar.md) مدخل **Web Engineering** غني، لكنها ليست معيار Software Engineering شاملًا. تقنيات مثل Redux/SSR/WebSockets خيارات *مشروطة*، وليست ضوابط إلزامية.
- لا نهدف إلى كتابة «موسوعة تعليمية» داخل prompt؛ نهدف إلى **قواعد اختيار + معايير قبول قابلة للاختبار + حدود سلطة**.
- مبادئ جودة المنتج توضع في طبقة أعلى من أسماء الأدوات، ثم يتم الربط بـprofiles بحسب `web_frontend`، `backend_api`، `desktop`، `mobile`، `data_pipeline`، `cli_library`، `distributed_service` أو `specialized`.
- المراجع الخارجية للقياس والمراجعة: [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) (**نموذج جودة منتج ذي تسع خصائص، لا نسخة مجانية كاملة من المعيار**)؛ [NIST SSDF SP 800-218](https://csrc.nist.gov/pubs/sp/800/218/final)؛ [OWASP ASVS 5.0.0](https://asvs.owasp.org/) عند انطباق تطبيق الويب؛ [WCAG 2.2](https://www.w3.org/TR/WCAG22/) للويب؛ [SLSA v1.2](https://slsa.dev/spec/v1.2/) عند وجود build supply-chain؛ و[DORA metrics](https://dora.dev/insights/dora-metrics-history/) لمقاييس تسليم أنظمة منتشرة.
- **لا ادعاء بالامتثال** لأي معيار لمجرد الإشارة إليه؛ الالتزامات القانونية والمجالية تُحدد لكل مشروع بعد مراجعة مختص.

## 2. التصنيف المعماري للجودة: 16 نطاقًا لا 16 إطار عمل

| ID | المجال الشامل | متى نفعّله؟ | أمثلة قرار/تحقق؛ لا تُفرض أداة بعينها |
| --- | --- | --- | --- |
| D01 | Product / Requirements Engineering | كل تغيير له سلوك مطلوب | هدف قابل للقياس، سيناريوهات قبول، رفض المتطلبات المتناقضة |
| D02 | Architecture & Boundary Design | كل تغيير؛ يزيد العمق بالمخاطر | حدود المجال والتبعيات، ADR عند قرار مؤثر، تجنب abstraction بلا حاجة |
| D03 | Code Quality & Maintainability | كل تغيير كود | مراجعة diff، code conventions، التحليل الثابت، عقد الواجهات |
| D04 | Frontend / Rendering / UI State | عند وجود واجهة ويب | اختيار CSR/SSR/SSG عند الحاجة، حالة العميل، hydration |
| D05 | Backend / API / Domain Logic | عند وجود خدمات أو API | idempotency، validation، authz، contract testing |
| D06 | Database & Data Engineering | عند تخزين/ترحيل/استخراج بيانات | migrations، الاتساق، provenance، dedup، فقد السجلات |
| D07 | Networking / Distributed Systems | عند الاتصال الخارجي أو التوزيع | timeouts، backpressure، 429، partial failure، retry safety |
| D08 | Security & Privacy | كل مشروع؛ عمق حسب البيانات والتهديد | أسرار/صلاحيات/تهديدات/حدود ثقة؛ تطبيق ASVS عندما ينطبق |
| D09 | Performance / Capacity | عندما توجد حدود زمن/حمل أو خطر أداء | budgets ومقارنة p95/baseline، CWV لواجهات الويب |
| D10 | Reliability / Recovery | عندما توجد عمليات دائمة أو متكررة | restart/crash, backup/restore, timeout، recovery/rollback |
| D11 | Verification / Test Engineering | كل تغيير يمكن التحقق منه | RED→GREEN أو assertions مناسبة، regression، negative tests |
| D12 | Build / CI / Release / Supply Chain | عند بناء أو نشر artifacts | lockfile، dependency audit، provenance، توقيع متناسب |
| D13 | Observability / Operations | عند وجود استخدام وتشغيل مؤثر | logs/traces/alerts بلا تسريب، incident diagnosis |
| D14 | Usability / Accessibility / I18N | عند وجود مستخدمين أو لغات | keyboard, labels, RTL, locale؛ معايير الواجهة الفعلية |
| D15 | Governance / Cost / Compliance | كل تغيير بحسب أثره | owner، التراخيص، الخصوصية، تكلفة التنفيذ، عدم توسع |
| D16 | AI Agent Authority / Evidence | كل مهمة يقودها AI | untrusted outputs، نطاق أدوات، موافقات، أدلة source/test صريحة |

**التغطية النظرية:** 16 نطاقًا تنظيميًا مقترحًا، **وليست** 16 شهادة امتثال. بعض الـ180 مفهومًا يدخل تحت أكثر من نطاق (مثل cache: D04/D06/D07/D09)، ولا نكرر طلب تطبيقه.

## 3. متطلبات تشغيل قابلة للتتبع

التصنيفات: **P0** ضرورة منهجية قبل ادعاء أي نجاح؛ **P1** إلزام عند وجود سطح/خطر مطابق؛ **P2** خيار عند ضرورة مثبتة. `P0` ليس أمرًا باختبار جميع أنواع التطبيقات أو إضافة كل الأدوات.

| ID | مستوى | متطلب واضح | دليل قبول محدد | المصدر/الفجوة |
| --- | :---: | --- | --- | --- |
| UER-01 | P0 | يحدد نوع المشروع ولغاته ومنصته ويعترف بالمجهول | قائمة stack & surfaces مع `unknown` و`not_applicable` | D01/D16 |
| UER-02 | P0 | يفصل المطلوب من المستخدم عن الحل المقترح | نتيجة/معيار قبول متفقان دون افتراض مخفي | D01 |
| UER-03 | P0 | يستخدم الكود والمواصفات والـADR الفعلية في brownfield | paths/commit refs وحدود ما قرئ؛ لا افتراض APIs | D02 |
| UER-04 | P0 | يربط متطلبات الوظيفة باختبار/شاهد | لكل دعوى مهمة evidence أو `UNVERIFIED` | D11 |
| UER-05 | P0 | يختار من المجالات/180 ما ينطبق ويبرر استبعاد غير المنطبق | applicability map للأجزاء ذات الخطر؛ لا 180 علامة شكلية | D01–D16 |
| UER-06 | P0 | يقدم أصغر تصميم يلبي القبول؛ يعيد استخدام الموجود | alternatives + قرار رفض الاعتماديات/التعقيد بلا مبرر | D02/D15 |
| UER-07 | P0 | يحافظ على حدود الملفات وصلاحيات القراءة/الكتابة | scope diff + permissions، لا تعديل production بلا تصريح | D16 |
| UER-08 | P0 | يرفض استخدام مخرجات LLM كدليل اختبار أو صلاحية | test/tool/CI evidence منفصل عن model judgment | D11/D16 |
| UER-09 | P0 | يُظهر PASS/FAIL/BLOCKED/NOT_RUN مع المصدر والتاريخ | report من أوامر حقيقية وأكواد خروج، لا استنتاج | D11/D13 |
| UER-10 | P0 | يحقق شرط إغلاق محدد دون تمديد تلقائي | task closed إذا تحققت المعايير أو سبب فشل موثق | D15 |
| UER-11 | P1 | يحلل المخاطر الأمنية وحدود الثقة حسب النظام | threat notes + اختبار authz/secrets/injection عند انطباقها | D08 |
| UER-12 | P1 | يحمي بيانات العملاء والأسرار والاحتفاظ بها | data classification + scrub/privacy check | D06/D08 |
| UER-13 | P1 | يدير البيانات الدائمة والترحيلات دون فقد أو duplication | snapshots/constraints/migration test/rollback | D06/D10 |
| UER-14 | P1 | يصمم عقود API وtimeout وإعادة المحاولة بأمان | schema/negative 429/5xx/idempotency tests بحسب السطح | D05/D07 |
| UER-15 | P1 | يثبت أداء ضمن ميزانية مناسبة بدل فرض تحسين مسبق | baseline/p95 أو CWV measurement + threshold | D09 |
| UER-16 | P1 | يراعي الاستخدام وإتاحة واجهة المستخدم | keyboard/axe/manual/RTL checks عند انطباقها | D14 |
| UER-17 | P1 | يختبر حالات الفشل والتعافي للنظام الدائم أو المنشور | failure-mode and recovery checks مع stop conditions | D10 |
| UER-18 | P1 | يتحقق من سلامة الحزم والاعتماديات والنشر عند وجود build | lockfile/audit/build result/provenance بحسب الخطر | D12 |
| UER-19 | P1 | يوثق قرار تصميم معماري ذو أثر ويطلب مراجعة مستقلة حيث يلزم | ADR + reviewer evidence + قرار إنساني | D02/D16 |
| UER-20 | P1 | يجري اختبارًا تكامليًا/تعاقديًا عندما يعبر التغيير حدود طبقات | passing contract/integration tests أو blocker معلن | D05/D11 |
| UER-21 | P1 | يحمي بيانات المستخدمين وخصوصية telemetry عند الرصد | redaction/consent/retention checks | D08/D13 |
| UER-22 | P1 | يحدد مخاطر النشر وخطة rollback عندما تكون قابلة للتراجع | plan + live verification من البيئة المعتمدة | D10/D12 |
| UER-23 | P1 | يراجع عدم اختراق حد الاعتماديات والتراخيص | dependency/ownership/license diff | D02/D12/D15 |
| UER-24 | P1 | يراجع مفاجآت السباق/التزامن/الحالة عند انطباقها | concurrency/state transition test evidence | D04/D06/D07 |
| UER-25 | P1 | لا ينفّذ AI تغييرات حساسة دون موافقة صريحة وسلطة تقنية | documented approval + actual environment permission gate | D08/D16 |
| UER-26 | P1 | يختبر أصناف تدهور النظام ذات أثر للمستخدم | observed error/trace and alert/incident tests if live | D10/D13 |
| UER-27 | P1 | يحتفظ بربط المصدر واختبارات الفشل/النجاح وقرار الاعتماد | immutable git refs, file hashes, accepted result | D11/D16 |
| UER-28 | P1 | يسجل استثناء التزام/تنظيم متخصص بدل ادعاء Universal | domain-specific overlay with qualified owner | D15 |
| UER-29 | P2 | يستدعي مراجعين Goldfish أو نماذج متعددة عند ارتفاع مخاطر التصميم | verified fresh-context availability + useful source-backed findings | D02/D16 |
| UER-30 | P2 | يستخدم أدوات مواصفات متعددة المراحل فقط حين يكون التصميم معقدًا | reduction in missed requirements/rework vs overhead | D01/D02/D15 |
| UER-31 | P2 | يوثق تسليم العمل وقياس الإنتاجية إن كان منتجًا منشورًا | DORA measures and verified timestamps, not a guessed score | D12/D13 |
| UER-32 | P0 | يحترم النطاق المؤكد: لا تدريب ذاتي أو تغيير آلي للسياسات/الإصدار | no automatic policy/pin/knowledge promotion; [ADR-0006](../adr/ADR-0006-EVIDENCE-FIRST-NO-AUTONOMOUS-LEARNING.md) | D16 |

## 4. ما هو مُلزم دائمًا وما هو اختياري؟

المُلزم دائمًا: **التصنيف، الهدف، حدود الصلاحية، الدليل المناسب، سلامة النتيجة، إعلان غير المنفذ، إغلاق المهمة**. أما إعداد CDN أو GraphQL أو Service Worker أو تدريب نموذج أو EGM swarm أو تشغيل Docker فهي **ليست** متطلبات أساسية.

**تعريف أداة التطبيق الملائم**: `APPLICABLE` = يوجد جزء حقيقي من المنظومة قد يتأثر بالمبدأ؛ `N/A` = لا يوجد سطح؛ `UNKNOWN` = لم نستطع إثبات الغياب أو الحضور بعد. لا يجوز تحويل `UNKNOWN` إلى `N/A` لإظهار اكتمال زائف.

## 5. ملفات المتطلبات المقترحة — اختيارية إلى حين الاعتماد

```text
AGENTS.md                     # authority, project-specific instructions
.erei/PROJECT_PROFILE.md       # current stack and constraints, existing
research/...180-concepts...    # reference index (not pasted into each prompt)
task acceptance note           # only selected UER IDs + required evidence
CI / test tools                # actually perform checks
```

**لا نحتاج محرك routing أو policy engine جديد لهذه المرحلة.** يمكن البدء بتوجيه قصير للوكيل + اختيار UER IDs ذات الصلة من ملف مرجعي عند كل تغيير، والتحقق من نجاحه عمليًا قبل التفكير في تنفيذ آلي.

## 6. حدود هذا المستند

- متطلبات UER وD01–D16 **مسودة من صياغتنا**؛ لم تعتمد نهائيًا ولم تُنفذ اختبارات قبول لها.
- وجود 32 متطلبًا لا يعني وجود 32 خطوة إلزامية في كل مهمة، ولا ضمان الوصول إلى أعلى جودة ممكنة في كل مشروع.
- المعايير الخارجية منشورة من جهات مرجعية لكن بعض نصوصها محمية بحقوق نشر؛ نستخدم روابط وتوجيهات أصلية ولا نعيد إنتاج نص معيار مدفوع.
