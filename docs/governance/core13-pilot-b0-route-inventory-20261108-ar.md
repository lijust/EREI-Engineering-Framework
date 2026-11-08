# Core13 PILOT-B — B0 Source/Execution Route Inventory (frozen)

**8 نوفمبر 2026 | الوضع: PRE_REVIEW، لا تنفيذ لمكوّنات J4/J4S القديمة.**

## 1. قرار بدء B بعد إغلاق A

تحققنا من [موافقة المالك بعد التشغيل #6713657840](https://github.com/lijust/EREI-3.2/issues/308#issuecomment-6713657840) ومن نتيجة [Root Docker GET-only #42418179869](https://github.com/lijust/EREI-3.2/actions/runs/42418179869). أُغلقت [الحزمة A #308](https://github.com/lijust/EREI-3.2/issues/308) بوضع `CLOSED_PASS_SCOPED_READ_ONLY`، وسُجلت A0–A3 مع G0–G3 = **8/16** بوابة معتمدة. لا يمنح هذا أي إذن لتشغيل كود AI أو إعادة استخدام Root Proxy كمسار تحكم عام.

نبدأ **B0 فقط**: حصر ما هو مسموح وما هو محظور في المسارات الحالية، دون إعادة بناء J4 أو Docker أو فتح مراحل F5B1 جديدة.

## 2. جرد مثبت المصدر (14 مكوّنًا)

كل مسار في `contracts/core13-pilot-b0-source-route-inventory-v1.json` يحمل Git blob SHA مستخرجًا من **الملف الفعلي** في فرع A قبل بدء B، وليس تقديرًا من الاسم. **تمت إعادة قراءة الملفات الـ14 ومطابقة SHA لكل منها.**

| المجموعة | المصدر | الاستنتاج المبني على الكود | سياسة B |
|---|---|---|---|
| J4 | `tools/core13_j4_known_worker_lifecycle.py` | `docker create`، `docker start --attach`، `docker rm --force` عبر `subprocess.run` | **DENY** من مدخل Pilot |
| J4S | `tools/core13_j4s_streaming_fixed_worker.py` | `subprocess.Popen(["docker","start","--attach",cid])` ويرث J4 | **DENY** |
| D2D2 migration | `tools/core13_j5_04f4d2d2_broker_only_lifecycle_migration_contract.py` | يعترف صراحة ببقاء مسارات Docker CLI المباشرة في J4/J4S | REVIEW_ONLY |
| D3B2A | `tools/core13_j5_04f4d2d3b2a_fixed_host_stream_broker.py` | تنفيذ Host subprocess حقيقي لمهمات ثابتة | DENY |
| D3B1 | `tools/core13_j5_04f4d2d3b1_fixed_broker_seqpacket_ipc.py` | Broker IPC تجريبي/Offline، وليس Docker acceptance | HISTORY_ONLY |
| D3A | `tools/core13_j5_04f4d2d3a_typed_fixed_lifecycle_model.py` | Typed offline lifecycle model | REFERENCE_ONLY |
| F5B1B | `tools/core13_j5_04f5b1b_root_broker_durable_create_hold.py` | يحتوي على HTTP POST ثابت نحو Docker داخل Root broker | DENY |
| F5B1F | `tools/core13_j5_04f5b1f_real_broker_fixed_create_no_start_hold.py` | عملية CREATE ثابتة من المالك بدون START | DENY |
| A2 | `tools/core13_pilot_a2_owner_real_dockerd_getonly_hold.py` | Root GET-only نجاح محلي محدود | **DENY** إعادة استخدامه داخل B |
| Source Gate | `tools/core13_selected_source_gate.py` | تحقق Git Source محدود عبر subprocess | REFERENCE_ONLY |
| Snapshot Gate | `tools/core13_consolidation_gate.py` | تحقق Offline Snapshot | REFERENCE_ONLY |
| Pilot Closure Gate | `tools/core13_pilot_closure_contract_gate.py` | Validation للحوكمة دون تنفيذ Docker أو نموذج | POLICY_DEPENDENCY |
| Workflow A2 | `.github/workflows/core13-pilot-a2-owner-real-secondary-getonly-hold.yml` | Owner-only Root manual، وليس باباً لتشغيل Pilot | DENY |
| Workflow consolidation | `.github/workflows/core13-mainline-consolidation-check.yml` | اختبارات Source Offline فقط | REFERENCE_ONLY |

## 3. المشكلة الفعلية في التكامل

**المأزق ليس نقص تشغيل Docker بعد نجاح A2.** المشكلة أن مسارات J4/J4S التي تستدعي Docker CLI مباشرة **ما زالت موجودة في المصدر**، وأن اختبارات Root-scoped أثبتت آلية ملاحظة محدودة لا تساوي فصل كل مسارات تنفيذ Worker عن المضيف. إعادة استدعاء J4 أو J4S من Pilot ستعيد فتح الخطر الذي أغلقناه تحليليًا، وتناقض الحدود الجديدة.

### قرار B0

- لا نزيل J4/J4S تاريخيًا؛ حذفها ليس مطلوبًا لتحقيق Pilot استشاري محدود، وقد يهدر أدلة اختبارات سابقة.
- **B1 يجب أن يكون مدخلًا واحدًا جديدًا أو إعادة استخدام مدخل موجود مثبت بالكامل**، Default-Deny. يُسمح فقط بتحليل بيانات مصدرية/مخرجات نصية وإنتاج توصية **دون تنفيذ أو تطبيق**.
- ممنوع استيراد أو استدعاء J4/J4S/F5B1B/F5B1F/A2 من مدخل Pilot؛ ممنوع Shell/Root/Docker Socket/START/CREATE.
- أي Route مجهول يصل إلى المدخل الجديد = **BLOCK**، لا يُفترض أنه محمي.
- لاحقًا يمكن تقييم جودة AI في C على حالات مُسجلة؛ هذا **منفصل** عن اختبار منع التشغيل.

## 4. حدود اكتمال الجرد

تم استخدام GitHub Compare من `main` إلى فرع A؛ أعاد **300 ملف فقط** (حد عرض) ضمن مسار كبير متشعب، ثم فحصنا 14 ملفًا ذا أولوية بواسطة `fetch_file`. لذلك هذا **جرد مصدر مرتكز على الـPilot والاختناقات الأهم**، وليس إثباتًا لاكتمال شجرة كل مستودع أو الوصول إلى كل Execution Entry Point.

حتى يثبت B1 أن **نقطة Pilot الوحيدة لا تستطيع استيراد أو الوصول إلى Legacy/Unknown**، سيظل `PILOT_REACHABILITY=NOT_ESTABLISHED`، ولا نعلن B `CLOSED_PASS`. وجود Code قديم في المستودع **ليس دليلًا على إمكانية الوصول إليه من مدخل Pilot**؛ معيارنا هو الرسم الذي سنثبته في B1، وليس إزالة كل الملفات القديمة.

## 5. شروط إغلاق B0

1. وجود سجل JSON مثبت لـ14 مسارًا مع Source Git Blob مطابق ومصنّف، وسبب الثقة/المنع.
2. Negative evidence يثبت أن J4/J4S/Root broker مسارات Docker/Host مباشرة لا تليق بمدخل Pilot؛ لا طلب تجربة CREATE/START لإعادة إنتاج الحقيقة المصدرية.
3. توثيق مخاطر اكتمال الجرد وحدود GitHub Compare = 300، ومجموعة `UNKNOWN=DENY`.
4. اختبارات CI Nonroot تتحقق من مصدر الـJSON والـSHA والسياسة، دون Runtime Root/Docker؛ وتشير بوضوح إلى عدم ثبوت B1 Reachability بعد.
5. اعتماد المالك في [Issue #309](https://github.com/lijust/EREI-3.2/issues/309) بعد مراجعة الأدلة، ثم يتقدم B1. لا تُحتسب مرحلة B0 Pass من الوثيقة وحدها.

## 6. حد التوقف والحالة

```text
PACKAGE_A=CLOSED_PASS_SCOPED_READONLY
GATES_PASSED=8/16
PACKAGE_B=B0_PRE_REVIEW
PILOT_B1_SINGLE_ENTRYPOINT=NOT_IMPLEMENTED
LEGACY_J4_J4S_DOCKER_CLI_REMOVED=false
PILOT_REACHABILITY_TO_LEGACY=NOT_ESTABLISHED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```

**التالي المحدد:** مراجعة B0، ثم بناء/اعتماد سياسة B1 لمسار استشاري واحد **دون Docker أو تنفيذ كود مرشح**؛ لا ترحيل J4/J4S ولا بناء Root Broker جديد في هذه الحزمة.
