# Core13 PILOT-CLOSE v1 — سجل البداية والتحقق من الحوكمة

**7 نوفمبر 2026 | الحالة: Governance PR جاهز للمراجعة، وليس إذنًا لتشغيل A/B/C.**

## دليل إنشاء المنهجية فعليًا

| العنصر | الحالة المثبتة |
|---|---|
| سياسة عربية موحّدة في المستودعَين | Git blob SHA **c9f0c5385b6338ab61f8a1f14058b5c3e57b0545** مطابق بين App وFramework |
| عقد JSON محدد ثلاث حزم | Git blob SHA **939a27b43f752210668f6f8c0773209422f74209** مطابق بين المستودعَين |
| Validator غير متصل بالإنترنت | source pin SHA **b382f283fc32b3bb3b17a9c43ca36473804e3973** في App فقط |
| اختبارات منع توسع النطاق وترقية صلاحية AI | **21/21 PASS** وفق Log عمل GitHub Actions |
| التشغيل الموثّق | [GitHub Actions #42303291639](https://github.com/lijust/EREI-3.2/actions/runs/42303291639) — SUCCESS، Job **128186236279** |
| ما الذي أثبته التشغيل | صحة شكل العقد، منع حزمة رابعة، منع GO بلا أدلة، منع Stable/AI promotion، ومنع دورة علاج ثالثة دون تغيير العقد |
| ما الذي لم يثبته | لا Root، لا Docker، لا توقيع بشري، لا اكتمال A/B/C، لا مصداقية خارجية لسجلات منقولة إلى JSON |

## لوحة تحكم الإغلاق (لا تُستبدل بمؤشر عدد الاختبارات)

**المجموع ثابت: 16 Gate** = 4 حوكمة G + 4 حزمة A + 4 حزمة B + 4 حزمة C.  
**Formal GATE_PASS عند الإصدار الأول: 0 من 16**، لأن اختبار JSON لا يثبت إغلاق أي Gate بالشكل البشري المطلوب.

| المجموعة | Gates | نتيجة الإغلاق الأولية |
|---|---|---|
| Governance | G0 G1 G2 G3 | PROPOSED; **G3 يتطلب توقيع المالك** |
| A | A0 A1 A2 A3 | NOT_STARTED; عمل F5B1K القديم #305 صار تحت [#308](https://github.com/lijust/EREI-3.2/issues/308) |
| B | B0 B1 B2 B3 | NOT_STARTED; [#309](https://github.com/lijust/EREI-3.2/issues/309) |
| C | C0 C1 C2 C3 | NOT_STARTED; [#310](https://github.com/lijust/EREI-3.2/issues/310) |
| Stable | مسار مستقل خارج عداد الـ16 | DEFERRED; [#311](https://github.com/lijust/EREI-3.2/issues/311) |

**Issue الإدارة:** [#307](https://github.com/lijust/EREI-3.2/issues/307).  
**PR App:** [#312](https://github.com/lijust/EREI-3.2/pull/312).  
**PR Framework:** [#172](https://github.com/lijust/EREI-Engineering-Framework/pull/172).

## حسم التعارض بين `PASS` و`CLOSED`

- CI PASS = العقد صالح **بنيويًا فقط**؛ لا يغني عن إدخال الأدلة الفعلية ومراجعة المالك.
- اختبار أمني سلبي فاشل = Gate FAIL/BLOCKED، حتى إن باقي الاختبارات PASS.
- A/B/C = CLOSED_PASS **فقط بعد** كل الـGates الأربعة المرتبطة، وبمراجعة وتوقيع.
- إن لم تنجح A، قرار المشروع PILOT_NO_GO أو PILOT_BLOCKED، وليس فتح مرحلة أمنية جديدة.
- إن نجحت A/B/C، النتيجة القصوى **PILOT_ADVISORY_ONLY_GO**، مع AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE وstable_ready=false.
- لا تقدم مكتمل في جودة النموذج أو Stable يثبت من هذا التشغيل.

## أمر التنفيذ التالي بعد قبول العقد

**الخطوة المكتوبة التالية الوحيدة هي A0:** تثبيت التصميم المصغر لقراءة Docker الحقيقي عبر Proxy GET-only وإدراج source pin + threat model + cleanup. لا يبدأ اختبار A2 Root/Docker حتى تتوافر A0/A1 والأذن اليدوي من المالك. لا يُنشأ حرف F5B1 جديد.

**ملاحظة:** لا يكتب Validator إلى ملفات المشروع، ولا يتحقق آليًا من صدق اعتماد المالك أو من صحة محتوى GitHub Jobs؛ لذلك لا يُسمى Independent Attestation.
