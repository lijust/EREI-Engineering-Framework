# Core13 Pilot-A / A2 — real disposable Docker GET-only owner-manual contract

**7 نوفمبر 2026 — Candidate implementation, NOT_EXECUTED.**  
المسار الوحيد للحزمة A. لا نفتح F5B1L أو مرحلة رابعة.

## نطاق التنفيذ المحجوز مسبقًا

- تشغيل `dockerd` حقيقي **ثانوي منفصل** داخل مسار مؤقت حصري `/run/core13-j504e2a-*`؛ تظل Docker Host context/root كما كانت قبل/بعد الاختبار. `dockerd` يعمل Root ويستخدم kernel المضيف؛ **ليس Sandbox مستقلاً لحماية الكود غير الموثوق**.
- استعمال وظائف daemon المعتمدة سابقًا `_temporary_disposable_root`, `_daemon_argv`, `_wait_ready`, `_owned_pid`, `_read_private_info`, `_host_still_baseline`. لا تُكتب نسخة أخرى من مشغل daemon.
- User accounts Linux الثلاثة: `runner` Controller، `nobody` Worker، `daemon` Verifier؛ **UID/GID مختلفة**. يُرفض أي نقص أو تطابق بلا إنشاء حسابات بديلة.
- Docker socket ثانوي `test-daemon.sock` مملوك Root بالوضع `0600`. Proxy مستقلة `SOCK_SEQPACKET` مع GID خاص بـVerifier `0660`، وتتأكد من **PID+UID+GID** للـVerifier عبر `SO_PEERCRED`. Controller وWorker ممنوعان من الوصول إلى Key/Proxy/Docker daemon socket.
- Verifier يرسل **طلب رفض واحد** `POST /containers/create` (يرد Proxy بوضوح DENIED بدون إرساله إلى Docker)، ثم يستعلم مرتين عبر `GET /containers/json?all=1` فقط. Root Proxy يقرأ استجابة حقيقية من socket daemon الخاص عبر `b1b._docker_http` و`SO_PEERCRED` ويتأكد أن `[]`. HTTP arbitrary forward/inspect أو POST/START/DELETE **غير متاح في هذا التنفيذ**.
- إيصال محدود Local HMAC مع nonce واسم الـschema وUID Verifier وهوية daemon الفعلية PID + BootID + `/proc/<pid>/stat` start_ticks، و`terminal=UNRESOLVED`. Root يخزن الإيصال في ملف خاص مؤقت `0600` مع `fsync`، ويسترجعه، ويختبر رفض Controller وWorker.
- لا بيانات وحدة عقارية، لا نموذج AI، لا image pull، لا containers، لا CREATE وSTART وDELETE، ولا تعديل F5 WAL. Root يملك المفتاح؛ **ليست مستقلة أمنيًا عن Root** وليست crash-durable append-only.

## المعايير الحاسمة

| Gate | الشرط الصارم |
|---|---|
| **A2-0 manual authority** | Owner GitHub actor `lijust`، owner-only `workflow_dispatch` من branch ثابت وInput منفصل بمراجعة الحوكمة G3 ونطاق GET-only، إضافة إلى source pins قبل sudo؛ **لا يُعد هذا اعتماد G3 النهائي آليًا** |
| **A2-1 real secondary** | daemon PID + BootID + start_ticks + private socket/root/driver verified؛ بداية ونهاية Inventory فارغة؛ default host unchanged |
| **A2-2 real Unix separation** | ثلاث هويات مختلفة؛ رفض Controller وWorker لمفاتيح Proxy/Docker/Receipt؛ Verifier PID+UID+GID kernel exact؛ صفر FD leaks أو method bypass |
| **A2-3 GET-only** | GET حقيقي مرتين عبر Proxy خاص؛ الرد `[]` بعد التحقق من Docker الحقيقي؛ mutation denied ولم تصل daemon |
| **A2-4 final evidence and cleanup** | Run URL + Job ID + decoded logs + source SHA+negative evidence+root-only receipt+cleanup of exact generated private root، وعدم مساس Host Default Docker |
| **A2-5 ownership decision** | مراجعة بشرية مستقلة في Issue #307 / #308؛ تعيين `A2_GATED_PASS` فقط إن كل الأدلة موجودة، وإلا `BLOCKED/NO_GO` |

**مانع التشغيل حتى الآن:** G3 Owner signoff لم يُسجل على GitHub؛ لذلك استعدت وظائف Root تحت owner-manual gate فقط، ولا يجوز تنفيذها آليًا عند push/PR.

## فحوص غير مميزة بالصلاحيات

A2 Source-only CI تختبر بصمات مكونات سابقة، سياسة GET المحددة، رفض POST/START/DELETE وHTTP Query، رفض تجاوز Scope ومعرّف daemon/nonce/HMAC/تصريح تنفيذ الكود. **هذه ليست Evidence لـReal Docker GET**؛ لا يثبت A2 إلا بالـowner-manual Job الذي يقرأ Docker الحقيقي.

## حدود الإغلاق

```text
PILOT_A2_OWNER_MANUAL_REAL_SECONDARY_DOCKER=NOT_EXECUTED
PILOT_A2_SOURCE_AND_NONROOT_NEGATIVE=CI_PENDING
G3_OWNER_SIGNATURE=NOT_RECORDED
A0_A1_FORMAL_GATES=CLOSED_PASS_NOT_ESTABLISHED
A2_FORMAL_GATE=CLOSED_PASS_NOT_ESTABLISHED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_ESTABLISHED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
stable_ready=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```

**Hard stop:** إن فشل الاختبار أو تطلب صلاحيات جديدة، تُراجع إصلاحات في حدود **دورتين للحزمة A**، وإلا `CLOSED_NO_GO` أو `CLOSED_BLOCKED`، بلا B1L/B1M. لا يتم الانتقال إلى B دون قرار A موثق.
