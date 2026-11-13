# مصفوفة القدرات والتداخل — EREI مقابل سبعة مشروعات مفتوحة المصدر

**التاريخ:** 2026-11-13  
**الحالة:** `DOCUMENTED_CAPABILITY_REVIEW`، لا benchmark تشغيل.  
**المعيار المرجعي:** [UER-01..32](./ai-engineering-universal-requirements-20261113-ar.md) + [المجالات الـ180](./web-engineering-9-domains-180-concepts-ar.md).

## 1. كيف نقرأ المصفوفة؟

- `D` = القدرة موصوفة صراحةً في مستند رسمي/كود تمت قراءته، **ولا يعني أنها اختُبرت أو تحقق أداؤها**.
- `P` = قدرة جزئية أو مشروطة أو لا تنطبق إلا بتخصيص.
- `?` = **غير مثبت من المصادر المفحوصة**؛ لا يعني غير موجود.
- `H` = بحث أو تجربة محدودة محليًا (فقط في مكونات Core13، لا production certification).
- لسنا بصدد منح درجة نجومية أو ترتيب شعبية أو مجموع رقمي يخلط جودة التنفيذ مع حجم الميزات.

**الاختصارات:** `E` = EREI Framework، `S` = GitHub Spec Kit، `G` = Google EGM، `O` = OpenSpec، `B` = BMad، `U` = Superpowers، `A` = Agent OS.

| قدرة UER مميزة | E | S | G | O | B | U | A | الدليل الأساسي والتفسير |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | --- |
| قواعد ودستور دائم لكل مشروع | D | D | P | D | D | P | D | EREI constitution؛ Spec Kit constitution/presets؛ OpenSpec config؛ Agent OS standards |
| مشروع موجود: اكتشاف الكود والمعايير | D | P | D | D | D | P | D | EREI `project-standard-discovery`؛ EGM bootstrap/drift؛ OpenSpec existing-projects؛ Agent OS |
| بدء مشروع وكتابة متطلبات قابلة للاختبار | D | D | D | D | D | D | P | EREI workflows؛ Spec Kit specify/plan؛ EGM draft؛ OpenSpec proposal/spec؛ BMad plans |
| اكتشاف أثر المعمارية ومراجعة YAGNI | D | P | D | P | D | D | P | EREI impact-analysis/quality؛ EGM Zoom Out معيار واضح |
| مراجعة مستقلة بسياق fresh حقيقي | P | ? | D | ? | P | P | ? | EGM Goldfish يتوقف إذا غابت أداة subagent؛ لا يعني oracle مستقلًا |
| مراحل feature/change متكاملة | D | D | P | D | D | D | P | EREI feature-development؛ Spec Kit core؛ OpenSpec opsx؛ Superpowers |
| تصحيح عطل مع RED/GREEN | D | D | P | P | D | D | P | EREI bug-fix/verification؛ Spec Kit bug extension؛ Superpowers TDD |
| معايير ويب مفصلة لكل تقنية من الـ180 | P | P | P | P | P | P | P | جميعها عامة/قابلة للتخصيص؛ **لا دليل أن أي أداة تتضمن الـ180 + قواعد انطباق + اختبار لكل بند** |
| معايير متعددة المنصات ومجالات البيانات | P | P | P | P | P | P | P | تحتاج project-specific standards/overlays ومرجع نوع المشروع |
| ربط متطلبات الجودة باختبارات/أوامر محددة | D | D | P | P | P | D | P | EREI verification before completion؛ Spec Kit tasks/analyze؛ Superpowers verify |
| التحقق من أن الاختبارات أُجريت لا مجرد ادعائها | D | P | P | P | P | D | ? | EREI evidence contract / Superpowers verification; **لا تفترض تطبيق الآلية دون تنفيذ فعلي** |
| اكتشاف drift بين الوثائق والكود | P | P | D | P | P | P | P | EGM drift-report مهارة صريحة؛ إمكانية عامة لا تحقق آليًا |
| threat modeling وحدود الأمان | D | P | P | P | P | P | P | EREI threat-model/security-review/constitution؛ معايير NIST/ASVS خارج الأطر |
| ضبط صلاحيات التنفيذ والعمليات الحساسة | D/H | P | P | P | P | P | P | EREI stable policies، Core13 تجارب advisor-only؛ **لا شهادة عزل شامل** |
| تسجيل أدلة source hashes ونتائج الاختبارات | D | P | P | P | P | P | ? | EREI durable evidence; Spec Kit وثائق تحقق؛ المعيار الحقيقي يتطلب tool receipts |
| ترقية موثوقة / إغلاق / rollback | D | P | P | P | P | D | P | EREI upgrade contract؛ Superpowers finishing branch؛ deployment checks مشروع-محددة |
| بوابة مستقلة لتأثير الأداء والأمان والإتاحة | P | P | P | P | P | P | P | أي إطار يحتاج Lighthouse/axe/security tests وسياق المشروع؛ لا تستنتج امتثالًا من skill |
| لا تعلم ذاتي/تغيير سياسة تلقائي | D | P | P | P | P | P | P | EREI [ADR-0006](../adr/ADR-0006-EVIDENCE-FIRST-NO-AUTONOMOUS-LEARNING.md) يثبت النطاق |

**ملاحظة حاسمة:** `D` يوثق وجود وظيفة أو قواعد؛ **ليس نتيجة اختبار native أو ضمان سلامة/إلزام**. وبالأخص `D/H` لا يعني أن Core13 يستطيع تشغيل أي نموذج/كود خصومي بأمان.

## 2. الأدلة الدقيقة التي تغيّر القرار عما افترضناه سابقًا

1. **EREI ليس مجرد logging/permissions**: لديه `constitution/ENGINEERING_CONSTITUTION.md` بعدد **20 مبدأ C-001..C-020**، ومهارات `project-standard-discovery`, `engineering-quality-review`, `verification-before-completion`. هذا مصدر قواعد وقرار بالفعل؛ ليس من المنطقي استبداله بمجرد تشابه أسماء أدوات أخرى.
2. **EREI feature-development ليس ناقصًا أصلًا**: `workflows/feature-development/WORKFLOW.md` يحتوي 15 مرحلة، مع **abbreviated path للمخاطر الصغيرة**؛ `workflows/bug-fix/WORKFLOW.md` يحتوي 13 مرحلة. لذا فرض Spec Kit أو OpenSpec الآن قد يكرر دورة حياة كاملة دون قيمة إضافية.
3. **Spec Kit أكثر قابلية للتجزئة مما ظننا**: `extensions/bug/README.md` يحدد `assess→fix→test`؛ `extensions/assess/README.md` يعمل قبل SDD لا كشرط عليه؛ `presets/lean/README.md` يوفر process أقصر. هذه قدرات بديلة لو ثبت نقص دورة EREI.
4. **EGM يملك ميزة اختصاصية حقيقية**: Review بـfresh-context Goldfish مع `zoom-out-standard`، `implementation-readiness-standard`، `drift-report`. لكن `docs/harnesses.md` يذكر أن fresh-parent-turn isolation لا يضمن عزل ملفات تعليمات الاستضافة وأن بعض بيئات cloud لها فجوات.
5. **OpenSpec قابل للتخصيص بعقد منظم**: `docs/customization.md` يذكر config/context/rules/custom schemas، و`docs/agent-contract.md` يقدم JSON/CLI contract؛ قد يكون بديلًا جيدًا إذا كان المطلوب artifact/schema بدل تغيير workflow EREI.
6. **Superpowers يتداخل مع EREI**: `skills/test-driven-development/SKILL.md` و`skills/verification-before-completion/SKILL.md` يشترطان RED/GREEN وإثباتًا حديثًا؛ وظيفتهما شبه مكررة من مهاراتنا القائمة. استيراد كامل مهاراته يحتاج مراجعة صلاحيات وطريقة تفعيل.
7. **Agent OS يتداخل مع `project-standard-discovery`**؛ يمكن اقتباس فكرة فهرسة المعايير والتصنيف عند الحاجة دون تركيب طبقة جديدة.
8. **BMAD أكبر في نطاق الأدوار وإدارة التخطيط**؛ لا توجد أدلة هنا على أفضلية تخص هدفنا في مشروع فردي صغير، ومصفوفة هذا التقرير لا تقيس الزمن أو المعدلات.

## 3. فجوات فعلية ذات قيمة مضافة محتملة

| فجوة | تقييم الإثبات | المقترح الأدنى |
| --- | --- | --- |
| المعايير الـ180 لا تغطي بنية backend/data/desktop/mobile بتفصيل كاف | **مؤكدة من مجال الصور** | [16 نطاقًا + UER-01..32](./ai-engineering-universal-requirements-20261113-ar.md)، مع اختيار ما ينطبق فقط |
| لا يوجد دليل أن المشروع يحوّل المعايير إلى tests تلقائية لكل نوع مشروع | **غير مثبت**؛ لا نفترض أنه غير ممكن | لا نبني محركًا عامًا؛ ابدأ بمخطط اختيار + check commands قائمة |
| عدم وجود مراجع Goldfish فعلي بسياق مستقل داخل EREI | **فجوة وظيفية في المسار المتحقق** (لدينا مراجعات لكن لا evidence أنه fresh) | استخدم EGM review اختياريًا إذا سمح runtime، أو reviewer بشري مختلف |
| صعوبة إدراك كلفة إصدار قرارات/معايير طويلة لكل مهمة | **فرضية عملية** تحتاج قياس | brief task card مؤقت صغير بدل 180 بندًا في prompt |
| ضعف أدلة فاعلية نموذج Gemini: E1 استكشافي وP1-01 HTTP 503 | **مؤكد من الأدلة** | لا نضيف runtime؛ قياس فاعلية على مهمة جديدة حقيقية فقط بإذن |
| قدرة Core13 على العزل التنفيذي الشامل | **غير مثبتة**؛ فرق pilot advisory عن stable | احتفظ بمنع صلاحية التنفيذ الضار؛ لا تعتبر أي external skill منفّذًا آمنًا تلقائيًا |

## 4. مراجعة نسبية للمصادر / source anchors

**مستودعنا** — `lijust/EREI-Engineering-Framework`:
- `constitution/ENGINEERING_CONSTITUTION.md` Git blob `58031356a23895efdad54ca54b15dde92c342989` (20 principles).
- `workflows/feature-development/WORKFLOW.md` blob `bf8498cd01663cb3629e814c47df8fdf1f13514b` (15 stages/low-risk abbreviated).
- `workflows/bug-fix/WORKFLOW.md` blob `ccd3fd9d9ca4e0be3d1735c100282f11c71ad718` (13 stages).
- `skills/project-standard-discovery/SKILL.md` blob `80f0f1d63521c1291b98a07bf4ec3a46aec9384b`.
- `skills/engineering-quality-review/SKILL.md` blob `c00dbaad53faa70358ea5ea959730c11c2ab6a45`.
- `skills/verification-before-completion/SKILL.md` blob `f6192131db74c3c81b147f77e67bf18b54fa48ca`.
- `README.md` الحالي و`ADR-0006` يقران أن أثر AI التشخيصي والتشغيل المطلق غير مثبت.

**المشروعات المقارنة**:
- GitHub [Spec Kit Bug Extension](https://github.com/github/spec-kit/blob/main/extensions/bug/README.md) blob `363ff363b60fb7fbccb7e2c6c79eb9ae34f69eef`، [Lean preset](https://github.com/github/spec-kit/blob/main/presets/lean/README.md) blob `ab17257f96091590d2289699aaf2b114cc05bbbe`.
- Google [EGM README](https://github.com/google/elephant-goldfish-model/blob/main/README.md) blob `d570bc7dee8f29e09f243e6a6245976bb803da15`، [Zoom Out Standard](https://github.com/google/elephant-goldfish-model/blob/main/resources/document_standards/zoom-out-standard.md) blob `de01edd8c458730241dea17a2d7bcaad153c9f94`، [Harness constraints](https://github.com/google/elephant-goldfish-model/blob/main/docs/harnesses.md).
- Fission-AI [OpenSpec customization](https://github.com/Fission-AI/OpenSpec/blob/main/docs/customization.md) blob `93c055325dfc792c63e114f57f779b4c6576bda3`.
- obra [Superpowers TDD](https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md) blob `46838cc9e893c06259e3bdad0fc2425b36242f15`.
- BMad [README](https://github.com/bmad-code-org/BMAD-METHOD/blob/main/README.md) blob `bd9fbb40ccb25207194dc9ed88b24134f4ae3d0c`.
- Agent OS [README](https://github.com/buildermethods/agent-os/blob/main/README.md) blob `78e2756db5055ef039a6f94053e55187dc55fec1`.

## 5. حدود المراجعة والاستنتاج

المصفوفة مأخوذة من ملفات المستودعات الرسمية فقط، ولم يُختبر أي إصدار مثبت منها داخل بيئة EREI أو على جهاز المستخدم، ولم تُنفذ اختبارات قياس الجودة ومقارنة المخرجات. لا تُحسب `?` «FAIL»، ولا تُحسب `D` «VERIFIED_PASS». أقوى استنتاج هنا هو **وجود تداخل وثائقي ووظيفي كبير** مع Framework الحالي، مما يضع عبء الإثبات على من يقترح استبداله أو فرض منظومة جديدة.

**التوصية المشتقة:** احتفظ بـEREI كمرجع السياسة والمعلومات والتحقق الحالي؛ أصلح الفجوات الموضوعية في المعايير، ثم اختبر **EGM اختياريًا للمراجعات المستقلة** و**Spec Kit أو OpenSpec اختياريًا فقط إذا أظهر الواقع قصورًا في مسار EREI**. لا يُدمج أي plugin بالكامل قبل قياس القيمة على مهمة حقيقية.
