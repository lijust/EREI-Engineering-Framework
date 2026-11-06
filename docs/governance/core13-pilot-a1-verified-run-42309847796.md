# Core13 Pilot-A1 — دليل الاختبارات الفعلية (7 نوفمبر 2026)

**النطاق:** A1 الاختبارات السلبية على Linux Nonroot. **لا إغلاق رسمي لـG3 أوA1**، ولا تشغيل Docker حقيقي.

## نتيجة مستقلة من GitHub Actions

- [Run #42309847796](https://github.com/lijust/EREI-3.2/actions/runs/42309847796) — **SUCCESS**؛ Job `128208288295`.
- Decoded logs: **29 A1 kernel negative PASS** + **30 A0 policy PASS** + **21 Governance PASS** = **80/80 PASS**.
- اختبار `fork()` PID حقيقي و`SO_PEERCRED`، رفض CREATE/DELETE/START، CID خاطئ، query/header injection، حجم >256، `SCM_RIGHTS`، والتحقق الفعلي من عدم تسرب أي FD عبر `/proc/self/fd`، Socket symlink/mode=0666، timeout، وresponse limit.
- الـBackend **ثابت اصطناعي**، والـChild يحمل **نفس UID/GID**؛ محاكاة اختلاف UID/GID هي تغيير قيمة المقارنة المتوقعة فقط، وليست اختبار Kernel بين حسابين مستقلين.
- `real_docker_api_calls=0`، `owner_root_calls=0`، `model_execution=0`.

## تاريخ التصحيح دون إخفاء الإخفاقات

- [Run #42309509954](https://github.com/lijust/EREI-3.2/actions/runs/42309509954): FAIL بسبب `type(Path) is Path` في Source Gate.
- [Run #42309585968](https://github.com/lijust/EREI-3.2/actions/runs/42309585968): FAIL لنفس خطأ `PosixPath` في Unix Socket Gate.
- [Run #42309682376](https://github.com/lijust/EREI-3.2/actions/runs/42309682376): **79/79 PASS** بعد إصلاح الموضعين مع المحافظة على جميع القيود.
- [Run #42309847796](https://github.com/lijust/EREI-3.2/actions/runs/42309847796): **80/80 PASS** بعد إضافة شاهد فعلي يمنع تسرب FD.

**الإصلاحات التشخيصية قبل اعتماد G3:** دورتا CI تصحيحية لنفس السبب الجذري (مقارنة صنف Path بالهوية)، ومسجلتان بوضوح. الميزانية الرسمية لإصلاحات الحزمة لا تُفعّل قبل اعتماد G3؛ لا يجوز تصفير أي جولة معتمدة مستقبلاً بصمت.

## Source pins وحدود الإغلاق

- A1 source blob `419006a374688fe6988a8cd1efac54e87f8cd9c1`.
- A1 tests blob `71c956f1a28f32820247ee125adea53427f14e91`.
- A0 source blob `393140049b2a23ed8981e175b78df0bbb8702b94`.
- A0 contract blob `5b9af0c999afa636c735d7ac49ae5696a36f69bd`.

**A1_NONROOT_NEGATIVE_SCOPED_PASS_PRE_REVIEW** — وليس `A1_GATED_PASS`.
`G3_OWNER_SIGNOFF=NOT_RECORDED`، `A2_REAL_DOCKER=NOT_EXECUTED`، formal closure **0/16**.

`AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE`، `stable_ready=false`.
