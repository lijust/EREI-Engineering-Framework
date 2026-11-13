# تدقيق منظومة المستودعات التي تخدم جودة تنفيذ AI Engineering

**التاريخ:** 2026-11-10  
**الحالة:** Source-backed desk review / لا توجد تجارب تكامل أو تثبيت محلية مثبتة ضمن هذه المراجعة.  
**القرار المحمي:** لا تعديل لكود Framework أو EREI 3.2 ولا نقل Project pins أو منح صلاحيات جديدة بمجرد قراءة هذه المقارنة.  
**المسألة:** بناء أسلوب عام يوجّه أي AI coding agent إلى عمل احترافي يراعي التسعة مجالات *حين تنطبق*، مع أدلة تحقق قابلة للتكرار، بأقل هندسة إضافية.

## 1. طبيعة الفجوة: أداة التنفيذ ≠ مبدأ الجودة ≠ دليل تحقق

- **التوجيه/الدستور**: `AGENTS.md` ومعيار المشروع ونطاق التعديل يوضحان القواعد.
- **تنظيم المهمة**: Spec Kit أو OpenSpec أو BMAD أو Superpowers يحدد خطوات تحليل/تخطيط/تنفيذ؛ ليس أي منها ضمانًا آليًا لسلامة 180 مفهومًا.
- **مراجعة تصميم مستقلّة عن سياق المؤلف**: EGM/Goldfish عندما يتوفر fresh-context subagents بالبيئة؛ لا يعتبر اختبارًا حتميًا.
- **الحكم على العمل**: اختبارات مشروع حقيقية وقياسات أداء/إتاحة/أمان + مراجعة بشرية مستقلة بحسب المخاطر؛ مجرد checklist لا يكفي.
- **ضبط السلطة**: ضوابط البيئة/المستودع والرخص والصلاحيات البشرية، لا الثقة في مطالبة الوكيل بقراءة سياسة.

## 2. النتائج الموثقة من المشاريع الأصلية

| المصدر | القدرة المدعومة بنص المستودع | ما لا يثبته | موضعه المحتمل |
| --- | --- | --- | --- |
| [GitHub Spec Kit](https://github.com/github/spec-kit) (`README` blob `a4ea4f520add603de250c59f96037f0eb7be46e5`) | SDD متدرج: specify→plan→tasks→implement→converge؛ **Bug fixing** و**Idea assessment** مدخلان مستقلان عبر extensions اختيارية؛ constitution/presets/quality gates/integrations | مراجعة أمنية مستقلة أو تحقق من الأداء دون أدوات المشروع؛ ليس كل workflow إلزاميًا | **أفضل مرشح للعمود الفقري** عند اختيار عملية موحدة، لا يثبت التفوق إلا بقياس عمل فعلي |
| [Google Elephant–Goldfish Model (EGM)](https://github.com/google/elephant-goldfish-model) (`README` blob `d570bc7dee8f29e09f243e6a6245976bb803da15`) | مصمم بسياق Elephant ومراجعون Goldfish fresh-context، review/brainstorm/draft/drift/bootstrap، فحص Zoom Out وcomprehension وreadiness | ليس نموذج LLM بأوزان خاصة، ولا تنفيذ اختبار RED/GREEN أو عزلًا تشغيليًا؛ fresh subagents يتوقف عند غيابها؛ ليس منتج Google مدعومًا رسميًا | **مراجع اختياري مستقل للتصميمات المهمة** |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) (`README` blob `7b8da04ac27fb1fa5a9578303873559e0c1b6ad2`) | lightweight change specs (proposal, scenarios, design, tasks, archive)، brownfield-first، shared spec stores في beta | لا يثبت صحة الكود أو استقلال المراجعة؛ مسار specs يتداخل مع Spec Kit | **بديل Spec Kit الأخف** إذا أثبتت التجربة أنه أسرع لمشروعاتنا |
| [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) (`README` blob `bd9fbb40ccb25207194dc9ed88b24134f4ae3d0c`) | أدوار product/architecture/UX/QA وعملية متدرجة الحجم؛ يصف v6.12 stable وv7 preview alpha في هذه اللقطة | التكامل مع عدة workflows قد يعيد تضخم الأدوار؛ لا دليل خاص على 180 قاعدة | **مقارنة إضافية فقط** عند وجود فرق/منتج أوسع، وليس إضافة افتراضية |
| [Superpowers](https://github.com/obra/superpowers) (`README` blob `c5bb59fdaf17ba154e803c549cd71a73ef36c24b`) | مهارات التصميم وTDD RED/GREEN وYAGNI وDRY وخطط تنفيذ/مراجعة وقد يشغّل subagents على مهام متعددة | التشغيل الموصوف قد يصبح تلقائيًا وطويلًا؛ يتطلب فحصًا دقيقًا للصلاحيات قبل اعتماد المهارات | **بديل مسار تنفيذ/اختبار** لا يركب فوق كل workflows دون ضوابط |
| [Agent OS](https://github.com/buildermethods/agent-os) (`README` blob `78e2756db5055ef039a6f94053e55187dc55fec1`) | اكتشاف معايير المشروع وفهرستها وتقديم المعايير المناسبة عند العمل؛ توليد spec | ضخ تعليمات تلقائي قد يخلط نطاق المهمة؛ لا يعد سلطة خارج التعليمات الموثوقة | **أفكار لإدارة المعايير**؛ نفضل ملفًا واحدًا وقواعد اختيار بسيطة أولًا |
| [AGENTS.md](https://github.com/agentsmd/agents.md) (`README` blob `8ce701e74909d5f08e2810380e0ff15f547aa0c8`) | صيغة عامة خفيفة لتوجيه الوكلاء ببيئة التطوير والتجارب وتقاليد PR | لا ينفذ ضوابط بنفسه أو يلزم نموذجًا بالتعليمات | **نحافظ عليه مصدر توجيه**؛ لدينا AGENTS.md في المشروع بالفعل |
| [Awesome Copilot](https://github.com/github/awesome-copilot) (`README` blob `42eb735a4e168d135a90f7f8618c6847f681ec4d`) | فهرس community للـagents/instructions/skills/plugins | مكونات المجتمع غير مراجعة تلقائيًا ولا يُوصى بتثبيتها جماعيًا | كتالوج للاختيار عند حاجة محددة |
| [OpenAI Plugins](https://github.com/openai/plugins) (`README` blob بحسب مراجعة 2026-11-10) | مكتبة إضافات وأمثلة Codex منظمة وواجهات مساندة للمهارات | ليس نظام قواعد لتغطية كل المجالات؛ يحتاج تدقيق كل plugin | قدرات متخصصة حسب المشروع، لا بديل للدستور والاختبارات |
| [openai/skills](https://github.com/openai/skills) | سجل أمثلة تاريخي | **README يعلن أنه deprecated** ويوجه إلى `openai/plugins`؛ لا تبدأ تكاملًا جديدًا منه | **لا يُختار كأساس جديد** |
| [EREI Engineering Framework](https://github.com/lijust/EREI-Engineering-Framework) (أساس `README`، [ADR-0006](../adr/ADR-0006-EVIDENCE-FIRST-NO-AUTONOMOUS-LEARNING.md)) | دستور، أدوار، مخططات، سجلات وأدلة، اختبارات وتدرج صلاحيات؛ عقود مستقلة عن التقنية | ليست كل أجزاء Core13 مثبتة الفعالية؛ لا دليل أن بناء runtime جديد يحسن إنتاجية Codex مقارنة بالتجميع البسيط | احتفظ بالضوابط/الأدلة التي تخدم هدفًا فعليًا؛ **لا تستمر في توسعة متزامنة تلقائيًا** |

**مصادر التحقق:** قراءة `README.md` الأصلية وأدلة [Spec Kit الرسمية](https://github.github.com/spec-kit/) و[EGM harness/test status](https://github.com/google/elephant-goldfish-model/blob/main/docs/harnesses.md) و[EGM testing](https://github.com/google/elephant-goldfish-model/blob/main/TESTING.md). هذه مراجعة ادعاءات ومكونات من المصدر، **وليست benchmark أداء** أو تدقيقًا أمنيًا للكود الخارجي.

### إيضاحات تؤثر في قرارنا

1. **Spec Kit أكثر من SDD فقط بحلول 2026-11-10**: لديه عمليات bug fixing وidea assessment بشكل إضافات مستقلة اختيارية. لا نلزم كل إصلاح بسيط بمراحل specify/plan/tasks الكاملة.
2. **EGM آلية تصميم/مراجعة وليست engine بديلًا**؛ يتطلب subagents ذوي سياق جديد، وعمليات التحقق المحلية/المعرفية لا تعني عزل التعليمات المضيفة ولا صحة التنفيذ. بعض سجلات البيئات تترك Cloud/isolation غير مؤكد.
3. **OpenSpec يستهدف brownfield ويسمح بمواصفات خفيفة**؛ لكن تشغيله مع Spec Kit على نفس المهمة يخلق ازدواجًا لمصدر المتطلبات وخطط التنفيذ.
4. **Superpowers يقدم TDD مفيدًا ولكن مهاراته قد تُفعّل تلقائيًا**. لا نعطي إضافة خارجية سلطة تعديل المستودع أو تجاوز بوابة مراجعة/أمن.
5. **Agent OS يفيد في الفهرسة والانتقاء**؛ لا نضيف runtime لتوزيع 180 بندًا قبل اختبار استخدام جدول بسيط وتوجيه بالملف.

## 3. تحليل التداخل بالنسبة إلى أهدافنا التسعة

| المطلوب | التوجيه الأنسب | أداة تحقق مستقلة لاحقًا عند وجود السطح |
| --- | --- | --- |
| Rendering | اختيار استراتيجية في spec/architecture، Goldfish عند تعقيد معماري | اختبار hydration/SEO وقياس الظهور حسب stack |
| Performance | ميزانيات مناسبة في constitution/spec | Lighthouse/Web Vitals/Profiling + RUM عند وجود تطبيق منشور |
| State Management | قرار مفاضلة وغياب بيانات مكررة، وليس فرض مكتبة | component/unit/integration tests وحالات race/cache |
| Networking | contract + timeout/rate-limit/idempotency | API contract/chaos/fault-focused tests |
| Caching | TTL/keys/invalidation/خصوصية موثقة | اختبارات stale/permission/eviction/consistency |
| Architecture | Spec Kit للخطة، EGM عند قرار كبير | dependency checks + source review + اختبارات تكامل |
| Security | threat model + قواعد حدية في الدستور | SAST/dependency review/security tests/تدقيق مستقل |
| Accessibility | مواصفات قبول واضحة ومناسبة للغة | axe + keyboard + screen reader/manual + WCAG المناسب |
| Observability | تعريف ما يجب أن يظهر عند الفشل | CI/test run logs، traces/sampling وتحقيق حقيقي في الأخطاء |

## 4. لا تخلط التغطية المفهومية مع الامتثال

وجود نص `Check security` لا يعني أن XSS وCSRF وtoken leakage اختُبرت. ونفس الأمر لـWeb Vitals، keyboard access، retries بعد 503، ومراجعة cross-module contracts. يجب أن يُسجل لكل بند **applicable? → chosen technique → measurable evidence → pass/fail/unverified**. أما غير الملائم فيبقى `N/A` بسبب واضح.

## 5. استبعاد التكرار قبل التبني

- **اختر Spec Kit *أو* OpenSpec** لإدارة دورة المتطلبات في المشروع الواحد، لا الاثنين.
- **استخدم EGM فقط عند الحاجة لمراجعة مستقلة** لتصميم عالي الكلفة أو معقد؛ لا تستخدمه بدل اختبار كود.
- **لا تُركّب BMad + Superpowers + Spec Kit + OpenSpec معًا**؛ جميعها تنظم جزءًا كبيرًا من دورة العمل وتختلف في التعليمات والصلاحيات.
- **احتفظ بـAGENTS.md وملفات المشروع والقواعد الحالية** كمصدر أولويات، دون إعادة حقن سجل التعلم أو تغيير pinned Framework refs.
- **احتفظ بضوابط Core13 الموجودة بالفعل عند الحاجة إلى صلاحية/عزل خاص**؛ لكن لا تعتبر ذلك شرطًا لتشغيل كل إصلاح صغير.

## 6. محدودية هذا التقرير

لم ننفذ بعد مقارنة زمنية أو أمنية أو اختبار نموذج عبر المستودعات، ولم نثبت توافق أي إضافة على جهاز المستخدم أو مع سلاسل التعليمات الحالية. الملاءمة أعلاه **تقدير هندسي مستند إلى capabilities المعلنة وتصميم مشروعنا**، وليس نتيجة تجربة مقارنة مستقلة. يلزم فصل قرار اختيار الأدوات عن قرار تثبيتها أو منحها صلاحية كتابة.

مرجع الـ180 مفهومًا: [سجل المبادئ](./web-engineering-9-domains-180-concepts-ar.md). قرار التبني المرجح: [وثيقة التوصية](./ai-engineering-adoption-decision-20261110-ar.md).
