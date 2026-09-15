# Ownership methodology

Ownership observations are point-in-time issuer records with optional security scope. They preserve shareholder name, type, exact percentage when stated, threshold evidence when only a bound is stated, effective date, disclosure date and source document.

The allowed categories are state, founder, management, strategic, institutional, foreign and other. Classification requires direct evidence; the Ministry of Economy and Finance is classified as `STATE`, while the National Investment Fund remains `OTHER` because the source row alone does not establish the requested category safely.

The UZTL annual report says two shareholders each own more than 20%, but gives no exact percentage. The system consequently stores `>20` as threshold evidence and leaves `ownership_percentage` null. Top1, Top3 and free float are explicitly `UNAVAILABLE`; threshold bounds are not added together or converted into exact concentration. Historical queries filter on disclosure date so evidence cannot appear before publication.
