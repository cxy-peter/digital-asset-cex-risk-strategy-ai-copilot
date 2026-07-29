# CMS/STR 一键候选案件联动 Demo

> 该演示只在合成数据中创建内部候选案件，不连接生产 CMS，不向 MASAK 自动提交。

## 策略

- Strategy ID：`TPL-rapid_cashout_high_precision`
- Event：`ChainWithdraw`
- Level-3 Tag：`CMS_STR_CANDIDATE`
- Expression：`fiat_in_crypto_out_ratio >= 0.85 AND minutes_deposit_to_first_chain_out < 240 AND (withdraw_address_fraud_1hop_count >= 1 OR device_fraud_1hop_count >= 1 OR high_risk_chain_exposure >= 0.2)`
- Recommended Action：`RFI`

## 合成回测

- Alerts：153
- Precision：94.77%
- Recall：23.42%
- Alert Rate：1.53%

## 内部候选案件

- Enabled：`True`
- Case Count：`10`
- MASAK Feedback Status：`NOT_SUBMITTED`
- External Submission Allowed：`False`
- Automatic Filing Performed：`False`

| Case ID | User ID | Status | Evidence Hash |
|---|---|---|---|
| CMSSTR-TPL-rapid_cashout_high_precision-d9caaafdec | U0007857 | DRAFT_CASE | d8f737cfc09b… |
| CMSSTR-TPL-rapid_cashout_high_precision-b074d27c8a | U0006232 | DRAFT_CASE | 2137aa158d30… |
| CMSSTR-TPL-rapid_cashout_high_precision-dd955c634b | U0006191 | DRAFT_CASE | 543e2420ed1c… |
| CMSSTR-TPL-rapid_cashout_high_precision-88642ef7b7 | U0008358 | DRAFT_CASE | 0715bbabdbac… |
| CMSSTR-TPL-rapid_cashout_high_precision-25672874ca | U0009367 | DRAFT_CASE | 854e9ab704a1… |
| CMSSTR-TPL-rapid_cashout_high_precision-829013fb1f | U0005438 | DRAFT_CASE | 5d074735b5a9… |
| CMSSTR-TPL-rapid_cashout_high_precision-2b4eb16df5 | U0008201 | DRAFT_CASE | f33a0e107f0d… |
| CMSSTR-TPL-rapid_cashout_high_precision-7cd4bac178 | U0004899 | DRAFT_CASE | e23612f61d21… |
| CMSSTR-TPL-rapid_cashout_high_precision-9a183c30f0 | U0009775 | DRAFT_CASE | 55e620eefaaf… |
| CMSSTR-TPL-rapid_cashout_high_precision-39dafa5718 | U0000341 | DRAFT_CASE | 145edbdb6670… |

## 严格边界

- ‘一键 STR’在本原型中只表示预填内部 CMS/STR 候选案件；
- 最终是否形成 STR 必须由合规人员基于完整证据决定；
- 普通用户画像不得展示 STR 机密状态；
- MASAK 反馈字段只是状态模型，不代表发生了真实提交或反馈。