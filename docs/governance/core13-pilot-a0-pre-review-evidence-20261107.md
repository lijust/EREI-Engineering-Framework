# Core13 PILOT-CLOSE — أول تنفيذ بعد تجميد النطاق / A0 Pre-Review Evidence

**7 نوفمبر 2026.** هذا السجل هو الدليل الأول لتطبيق المنهجية **G0–G2 وA0**، وليس إثبات إغلاق G3 أو A0.

## نتيجة التنفيذ على GitHub

**[Run #42307806188](https://github.com/lijust/EREI-3.2/actions/runs/42307806188)**، Job **128201481701** = **SUCCESS**.

استخرجنا من سجل الـJob الفعلي:
- `A0_DISTINCT_CONTROLLER_WORKER_VERIFIER_OS_PRINCIPALS_NONROOT_PREFLIGHT_PASS` — حسابات runner / nobody / daemon موجودة على Linux runner وتختلف UID/GID، غير Root. هذه نتيجة **Nonroot preflight** فقط، وليست دليل عزل Root Proxy الحقيقي.
- `Ran 21 tests` / `OK` — اختبارات عقد الإغلاق العام G/A/B/C.
- `Ran 30 tests` / `OK` — اختبارات عقد A0 وGET-only ورفض تجاوز طُرق CREATE/START/DELETE ونطاق الـCID والـHostname والـQuery.
- **الإجمالي 51/51 PASS**. لا Docker runtime ولا sudo ولا Root ولا نموذج AI في هذه الجولة.

## ملفات العقد والأدلة الموحّدة

- `docs/governance/core13-pilot-closure-v1-ar.md` — نطاق G/A/B/C، 16 Gate، 2 rounds.
- `contracts/core13-pilot-closure-v1.json` — حالات إغلاق A/B/C **NOT_STARTED**.
- `docs/governance/core13-pilot-a0-readonly-docker-contract-ar.md` — Scope وThreat Model وAllowlist/UID/Bootstrap/Exit Criteria.
- `contracts/core13-pilot-a0-readonly-docker-v1.json` — تصميم A0 ثابت، `G3_AWAITING_AUTHENTICATED_SIGNOFF`.
- `tools/core13_pilot_a0_readonly_docker_policy.py` + `tests/unit/test_core13_pilot_a0_readonly_docker_policy.py` — تحقق offline فقط.

**قيد مهم اكتُشف وعولج قبل اختبار Docker:** إعادة استخدام UID `nobody` للعامل Worker والمراقب Verifier تضع مفتاح المراقب تحت سلطة العامل، ولذلك صار اختيار A0 الثابت **runner=Controller، nobody=Worker، daemon=Verifier**، مع اشتراط اختلاف UID/GID الفعلي، وعدم استعمال بدائل صامتة أو إنشاء حسابات على Runner.

## ما الذي يمكن اعتباره مكتملًا؟

| العنصر | التقييم الحالي |
|---|---|
| توثيق سياسة الإغلاق ومحاذاة المستودعين | PREPARED_AND_CI_CHECKED |
| G0–G2 | EVIDENCE_PREPARED — التوقيع غير موثق |
| G3 | **AWAITING_AUTHENTICATED_OWNER_SIGNOFF** |
| A0 تصميم GET-only | **DESIGN_AND_NONROOT_CI_PASS** — ليس GATE_PASS رسميًا |
| A1 اختبارات Linux/Unix سلبية شاملة | NOT_STARTED؛ اختبار العقد ليس بديلًا عن سلوك Proxy حقيقي |
| A2 Real secondary Docker GET-only | NOT_EXECUTED |
| A3 Outcome and owner report | NOT_STARTED |
| B وC | NOT_STARTED |
| Formal gate closure count | **0/16** |
| Stable وAI acceptance | **BLOCK_AI_ACCEPTANCE / stable_ready=false** |

## قرار الحركة التالية بلا توسع

العمل المكتبي/اختبارات Nonroot في A0 تم بإذن «ابدأ» الصادر في المحادثة. هذه العبارة ليست توقيع GitHub مستقل يمكن نسبه للمالك في السجل الرسمي؛ ولذلك لا أرفع G3 ولا أغلق A0 تلقائيًا.

**A1 (حزمة A نفسها) مسار التطوير التالي، وليس F5B1L:** اختبارات Kernel socket سلبية موجهة إلى HTTP Proxy مقيّد بطرق GET دون الوصول إلى Docker. بعد مراجعة G3/A0، تُنفَّذ A2 يدويًا بإذن مالك مستقل، مع كل شروط Source Pins وcleanup. لا يُنفذ Root بالنيابة عن المالك.
