# سجل التدخل وقياس التعرّض

Candidate source contract، إصدار 1، مرتبط بـF14 / Issue #80. يستخدم
`tools/learning_effectiveness.py` الموجود؛ لا خدمة أو قاعدة بيانات أو workflow جديد.
لا يغير هذا العقد السجلات التاريخية أو حالة تبني Candidate.

الغرض ربط finding وroot cause وDevelopment Output بالتنفيذ والتبني ومجموعة المهام
المؤهلة والنتائج الملحوظة. إكمال هذه السلسلة لا يثبت أن التدخل تسبب في تحسن.

## الإدخال

سجل JSON منفصل تملكه جهة قياس المشروع، وليس صفًا جديدًا في Task Learning ledger.
كل الحقول أدناه مطلوبة؛ الحقول غير المعروفة والتكرار في مفاتيح JSON مرفوضان.
يمكن أن تكون `adoption` هي `null` قبل تسجيل التبني، وأن تكون `tasks` فارغة.
المثال اصطناعي بالكامل ولا يمثل نتيجة تشغيل فعلية.

```json
{
  "schema_version": 1,
  "intervention_id": "fixture-intervention",
  "finding_refs": ["fixture:finding"],
  "root_cause": "fixture-root-cause",
  "development_output_ref": "fixture:development-output",
  "implementation": {
    "repository": "example/framework",
    "ref": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "adoption": {
    "repository": "example/project",
    "ref": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "implementation_ref": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "evidence": ["fixture:adoption"]
  },
  "cohort": {
    "repository": "example/project",
    "ref": "cccccccccccccccccccccccccccccccccccccccc",
    "ledger_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "epoch_id": "EPOCH-024",
    "eligibility_rule": "All material tasks in the declared epoch and workflow family",
    "selection_ref": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "tasks": [
      {
        "occurrence_id": "EOCC-20261020T010000Z-00000001",
        "identity_basis": "prospective",
        "exposed": true,
        "recurred": null,
        "evidence": ["fixture:occurrence-and-exposure"]
      }
    ]
  }
}
```

`implementation.ref` هو commit الإصلاح. `adoption.ref` هو commit تبنيه في المشروع،
و`adoption.implementation_ref` يشير إلى الإصلاح نفسه، وقد يختلف عن pin أحدث يحتويه.
`cohort.ref` يحدد نسخة دليل المشروع، و`ledger_sha256` يحفظ digest ملف المصدر كما هو.
`selection_ref` يحدد commit الذي وثّق قاعدة اختيار cohort قبل الاطلاع على نتائجها.
لا تستنتج الأداة ancestry أو تاريخ الاختيار أو تعرض مهمة بمجرد وجود هذه النصوص.

كل صف يخص occurrence واحدة في المشروع والـepoch المحددين. تُرفض الهوية المكررة.
`prospective` يتطلب هوية `EOCC`، و`legacy_assumed` يقبل `ETASK` أو `EOCC` لكنه يستبعد
دائمًا من مقامات prospective. هوية V2 وحدها لا تجعل backfill دليلًا prospective.
`exposed` و`recurred` يقبلان فقط `true` أو `false` أو `null`؛ الأرقام والنصوص لا تتحول
تلقائيًا إلى Boolean. `null` يعني غير مقيم، وليس عدم وقوع الخلل.

تُرفض exposure=true دون adoption، وتُرفض اختلافات مشروع التبني/cohort أو commit
الإصلاح المشار إليه. هذه فحوص اتساق داخل السجل، وليست مصادقة مستقلة على الأدلة.

## الحساب وحدود الاستنتاج

| المخرج | البسط | المقام |
| --- | --- | --- |
| exposure_assessment_coverage | مهام prospective التي قُيّم تعرضها true/false | جميع مهام prospective المؤهلة المسجلة |
| outcome_assessment_coverage | المهام المتعرضة التي قُيّم تكرار السبب فيها true/false | جميع المهام المتعرضة المسجلة |
| recurrence_rate_among_assessed_exposed | تكرارات السبب بين المتعرضة المقيمة | المتعرضة ذات outcome مقيم |

المقامات والأعداد تُشتق من الصفوف؛ لا تُقبل نسب نجاح جاهزة من الكاتب. المقام صفر
ينتج `null` للنسبة. الصفوف غير المتعرضة أو مجهولة التعرض لا تدخل مقام recurrence،
والصفوف التاريخية تظهر في `legacy_assumed_count` منفصلة. إذا كان التقييم جزئيًا،
تظهر `PARTIAL_OUTCOME_ASSESSMENT`؛ لا تُعرض النسبة الجزئية باعتبارها نتيجة cohort كاملة.

حتى مع اكتمال التقييم تكون الحالة `OBSERVED_OUTCOMES_ONLY`، مع
`effectiveness=NOT_ESTABLISHED` و`causation=NOT_ESTABLISHED` و
`evidence_authenticity=NOT_VERIFIED`. لا يستطيع validator اكتشاف حذف مهام مؤهلة من
سجل يقدمه الكاتب، أو توثيق صحة root cause أو مصدر الأدلة أو استيفاء observation window.
لهذا يلزم قبل استخدام النسب في قرار:

1. تثبيت eligibility وworkflow/risk families ونافذة الملاحظة قبل جمع النتائج.
2. مطابقة كل occurrence مع الدليل الأصلي ذي digest والـref المحددين، والتحقق من أن
   cohort تشمل جميع المحاولات المؤهلة، بما فيها failures وtimeouts وworkarounds.
3. مراجعة exposure لكل مهمة: هل نفذت النسخة التي تحتوي الإصلاح وهل مرّت بالمسار المعني؟
4. تقييم root cause مستقلًا عن النتيجة المطلوبة، وإظهار coverage والنواقص وتغير الاختبارات.
5. مقارنة cohorts متكافئة مع baseline أو control؛ لا يُستنتج الأثر من merge أو adoption.

المقاييس الأشمل مثل وقت التنفيذ وcost per verified task تبقى ضمن خطة benchmark
الموجودة في `governance/v2-remediation/MASTER_PLAN.md` عند اعتمادها. هذا السجل لا
يخترع baseline أو تكلفة، ولا يحول rework أو verification catches إلى execution accuracy.

## الاستخدام والتوافق

```text
python tools/learning_effectiveness.py --target PROJECT --before before.json --after after.json --intervention intervention.json
```

يطبق المدخل نفسه `require_active` قبل قراءة أي artifact، ويحتفظ بمخرجات المقارنة
السابقة دون تغيير عند غياب `--intervention`. عند وجوده يظهر قسم `intervention`
مستقل؛ لا تُربط صفوفه ضمنيًا بمجتمعات before/after ولا يرفع درجة ادعائها.
الدالة `assess_intervention` حساب pure لا يقرأ مشروعًا ولا يمنح إذن Candidate.

يعيد `prospective_cycle_status.py` حقولًا توضح أن `complete` تخص مراجع مراحل الدورة،
مع `cohort_exposure=NOT_ASSESSED` و`effectiveness=NOT_ESTABLISHED`. لا يعيد كتابة
`PROSPECTIVE_CYCLE_STATUS.json` أو يغير input schema الخاص به. الأدلة الحالية للدورة
تبقى محفوظة؛ لا تصنع الأداة بيانات لاحقة لـEPOCH-024.

## القبول والرجوع

هذه مرحلة مصدرية قبل قبول T01/T02/T04؛ استخدامها مع بيانات مشروع أو إعلان فعاليتها
يتطلب قبول التبعيات والتحقق من البيانات وCandidate activation. CI والمراجعة المستقلة
ما زالا مطلوبين. لا migration أو pin upgrade أو تشغيل model مدفوع ضمنها.

الرجوع إلى النسخة السابقة يعطل الخيار الاختياري، مع الاحتفاظ بسجل التدخل كدليل
منفصل؛ لا تحذف أحداثًا أو تغير fingerprints أو reviews لإتمام الرجوع.
