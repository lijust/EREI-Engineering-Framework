# قرار معماري مبدئي — احتفظ بـEREI، ولا تكرر Workflow بلا ضرورة

**التاريخ:** 2026-11-13  
**الحالة:** `PROPOSED_DECISION_FOR_OWNER_REVIEW`، وليست اعتمادًا أو تعديلًا لصلاحيات الإنتاج.  
**الهدف:** اختيار أقصر مسار للحصول على عمل هندسي عالي الجودة عبر تقنيات مختلفة من خلال وكلاء AI موجودين.  
**الأدلة المرجعية:** [متطلبات UER](./ai-engineering-universal-requirements-20261113-ar.md)؛ [مصفوفة المكونات](./ai-engineering-capability-and-overlap-matrix-20261113-ar.md)؛ [سجل الـ180](./web-engineering-9-domains-180-concepts-ar.md).

## 1. نتيجة البحث التي تغيّر توصية 10 نوفمبر

التوصية السابقة بجعل **Spec Kit العمود الفقري** كانت سابقة لمراجعة ملفات EREI الحالية على مستوى `constitution` و`workflows` و`skills`. بعد هذه المراجعة تبين أن EREI لديه بالفعل:
- دستور 20 مبدأ؛
- `project-standard-discovery` و`engineering-quality-review` و`verification-before-completion`؛
- `feature-development` بـ15 مرحلة وخيار اختصار قليل المخاطر؛
- `bug-fix` بـ13 مرحلة؛
- سجلات Evidence وقرارات ترقية المشروع.

**بالتالي لا يوجد مبرر مؤكد لاستبدال هذه المكونات بـSpec Kit الآن.** Spec Kit خيار ممتاز بمزايا extension/preset وlean، لكنه **منافس** لجزء من بنية EREI لا إضافة مكملة افتراضية. لا نثبت برنامجًا ثانيًا لتأدية دورة حياة ممتلكة بالفعل.

## 2. التداخل وما الذي يملأ فجوة حقيقية

| العمل الهندسي | ملكية الأنظمة المقترحة | القرار |
| --- | --- | --- |
| هوية المشروع ومصدر السلطة | `AGENTS.md` + `.erei/` المعتمدة + Git refs | **KEEP**؛ مصدر واحد فعلي لقواعد المشروع |
| الدستور والمخاطر والمسؤوليات | EREI Constitution وروتين المشروع الحالي | **KEEP**؛ لا نسخ constitution مستقلة بالتوازي |
| مفاهيم الجودة | [180 مفهومًا](./web-engineering-9-domains-180-concepts-ar.md) + UER-01..32 و16 نطاقًا مقترحًا | **GAP-FILL DOC ONLY**؛ لا runtime loader |
| اختيار ما ينطبق | EREI `project-standard-discovery` + بطاقة مهمة رشيقة | **REUSE / VALIDATE**؛ تصنيف سياقي لا إلزام 180 |
| إصلاحات بسيطة | existing bug-fix abbreviated path + deterministic tests | **KEEP**؛ لا Spec Kit أو Goldfish إلزامي |
| ميزات/تصاميم متوسطة | existing EREI feature-development | **KEEP** حتى يثبت تخلفه مقابل بديل |
| المراجعة المعمارية التي تحتاج منظورًا مستقلًا | Google EGM fresh-context Goldfish عند توافر native subagents | **OPTIONAL CANDIDATE**؛ قيد تحقق البيئة؛ فشل spawn = `NOT_RUN` |
| وثائق تصميم متوافقة مع كود تغير | EGM drift-report أو مراجعة مصدرية موجودة | **OPTIONAL** فقط عند Drift له أثر |
| تصنيف وتحليل ثغرات/اختبارات/CI | أدوات المشروع الأصلية + EREI verification | **KEEP**؛ لا يعتبر AI reviewer test oracle |
| دورة SDD أكثر قابلية للتخصيص أو موحدة خارج EREI | **Spec Kit أو OpenSpec كبديل** عند إثبات نقص المسار الموجود | **DEFERRED/OPTIONAL**؛ لا جمع الاثنين مع EREI على المهمة نفسها |
| Red/Green/code-review skill | EREI مهارات قائمة، Superpowers بديل محتمل | **NO DUPLICATE**؛ لا إضافة تلقائية |
| معيار تخصصي طبي/مال/سلامة أو بيانات حساسة | qualified domain overlay + owner/legal review | **NOT GENERALIZABLE**؛ لا ضمان بالمبادئ العامة |
| أمان اجرای كود LLM غير موثوق | موجود ضوابط أبحاث EREI Core13 غير مكتملة | **NO NEW SANDBOX**، لا تشغيل AI patches دون التفويض والتحقق |

## 3. تصميم تكاملي بلا محرك جديد

```text
  PROJECT SOURCE OF TRUTH (git + AGENTS.md + .erei/project docs)
                         |
              Existing EREI rules
                 + UER reference
                         |
     task-specific applicability (risk, project surface, selected UER IDs)
                         |
               existing coding agent
               + existing EREI workflow
                    /            \
               simple         material design
                 |                  |
              direct       optional fresh-context
             RED/GREEN      EGM review (if real)
                 |                  |
                 +---------+--------+
                           |
              scoped implementation
                           |
            actual project tests/CI
             + targeted checks where applicable
                           |
             evidence + human decision
```

لا نحتاج في هذه النسخة إلى model routing، RAG، semantic index، CI جديد، policy scripting أو إعادة كتابة workflows؛ **أيًا منها يحتاج فجوة مثبتة مستقلة**.

## 4. لماذا لا نبني حزمة واحدة تضم الجميع؟

- **Spec Kit/OpenSpec/EREI/BMad/Superpowers** تشترك في requirements/plan/implement/review، والخلط بينها ينتج مصادر حقائق مختلفة. اختيار مسار واحد للمهمة جزء من التحكم في المخاطر، لا مجرد تبسيط شكلي.
- **EGM** مختلف بقدر ما يوفر fresh-context review، لكن يضيف تكلفة تعدد الوكلاء، ونسخة ChatGPT Work/Cloud قد لا تعرض spawn فعلًا؛ لا ندّعي مراجعة مستقلة إن لم يثبت spawn.
- **Agent OS** يوزع المعايير، لكن EREI لديه `project-standard-discovery`. فلا حاجة لإضافة مصدر حقائق ثالث.
- **قائمة الـ180** ليست واجهة تنفيذ أو معيارًا إلزاميًا؛ ندعم project-specific profiles دون قواعد مجمدة لكل تقنية.

## 5. المخاطر والحدود التي لا يحلها اختيار أداة جاهزة

1. جودة التشخيص البرمجي الفعلي **غير مثبتة** في Core13: P1-01 انتهت HTTP 503 دون رد؛ P1-02 إصلاح بشري موجّه و4/4 GREEN، لا دليل على قدرة النموذج.
2. الـ180 تغطي الويب أكثر من قواعد البيانات/desktop/data pipelines؛ UER تسد **الهيكل** فقط، ولا تثبت الجودة العملية.
3. الوثائق `D` في [مصفوفة القدرات](./ai-engineering-capability-and-overlap-matrix-20261113-ar.md) لا تعني اختبار مستخدم محلي.
4. استقلال السياق لا يعني استقلال النموذج أو التعليمات الخفية. كل تقرير review يحتاج مصادر وقرار بشري.
5. لا يتم إثبات الأداء أو أمن API أو WCAG بمجرد اختيار إطار عمل؛ يستخدم المشروع أدوات فحص مناسبة.
6. تعذر GitHub Actions السابق لا يبرر ادعاء `CI_PASS` أو إزالة حماية الموافقة.
7. حفظ الأسرار ومصادر البيانات وتغييرات الإنتاج يظل ضمن الصلاحيات الحقيقية.

## 6. معايير لاستبدال عملية موجودة بدل تكديس أخرى

استبدل EREI feature workflow بـ **واحد فقط** من Spec Kit أو OpenSpec إذا ثبت على مهمات حقيقية أن:
- EREI الحالي يفوّت متطلبات قابلة للقياس أو يرفع إعادة العمل؛
- المرشح يغطي الفجوة دون خسارة evidence/permissions؛
- زمن الإنسان وكلفة المستندات لا تتجاوز الفائدة المقاسة؛
- لا يحتاج مصدرين متعارضين للحقيقة أو مرحلتين قسريتين للتعديل نفسه.

**Spec Kit مرشح أول للاختبار إذا احتجنا بديلًا** لوجود عمليات features/bugs/assessment ومجموعة presets، وOpenSpec بديل عند إثبات أن Spec Kit أعقد من الحاجة. لكن `FIRST` لا تعني `ADOPTED` أو أنه الأفضل مطلقًا.

## 7. الخيارات النهائية

| خيار | حكم مبني على الأدلة المتاحة الآن |
| --- | --- |
| استكمال بناء منصّة Core13 شاملة جديدة | **REJECT FOR NOW**: عبء إثبات الفائدة غير متحقق، ومخاطر صيانة كبيرة |
| استبدال EREI بـSpec Kit وEGM بالكامل | **REJECT FOR NOW**: خسارة العقود والضوابط، وتكرار القدرات |
| تركيب Spec Kit + OpenSpec + BMAD + Superpowers | **REJECT**: Overlap، تعارضات workflow وصلاحيات |
| **الاحتفاظ بـEREI الحالي + مراجع UER + اختبارات المشروع + Goldfish اختياري** | **PREFERRED CANDIDATE**: أقصر طريق مع أقل تغييرات؛ يحتاج تجربة محدودة |
| إضافة Spec Kit / OpenSpec بدل workflow محدد عند فجوة مثبتة | **CONDITIONAL LATER**: لا يسبقه تثبيت روتيني |

## 8. حدود اعتماد القرار

هذا القرار **مقترح بعد بحث مصدرّي وليس اعتماد تشغيل**. يتطلب قبول صاحب المشروع ووصول دليل تجربة حقيقية؛ لا تغيير لـ`main` أو `Stable` أو الـpin أو سياسات الصلاحيات أو تثبيت plugins خارجيًا. أما **توثيق المتطلبات** فمكتمل كمسودة قابلة للمراجعة.

الخطوة التنفيذية المحدودة: [بروتوكول اختبار واعتماد](./ai-engineering-bounded-validation-plan-20261113-ar.md). لا نخلق مشروعًا اصطناعيًا ولا نبرر بناء بنية إضافية لمجرد اختيار أداة.
