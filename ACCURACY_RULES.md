# UZQUANT — Accuracy Rules

These rules are permanent project policy.

They apply to every phase of UZQUANT development.

If any implementation request conflicts with these rules, these rules take precedence.

---

# 1. General Accuracy

1. Never invent financial data.

2. Never invent market data.

3. Never invent ownership data.

4. Never invent corporate actions.

5. Never invent APIs, endpoints, fields, documents, or datasets.

6. Never assume missing values are zero.

7. Missing information must remain explicitly missing.

8. If reliable analysis cannot be performed, return:

   `DATA INSUFFICIENT`

9. Facts, estimates, assumptions, and model outputs must remain distinguishable.

10. Uncertainty must be exposed rather than hidden.

---

# 2. Sources

11. Prefer authoritative primary sources over secondary sources.

12. Every material datapoint must retain source provenance whenever technically possible.

13. Source provenance should include relevant identifiers such as:

   - source
   - source URL or document ID
   - publication date
   - reporting period
   - retrieval timestamp

14. Search-result snippets are not sufficient evidence for material financial data.

15. Secondary sources must not silently override more authoritative primary sources.

16. Conflicting source values must be identified and logged.

17. Conflicts must not be silently resolved without a documented rule.

18. Do not infer that an API exists unless it has actually been verified.

19. Do not infer historical-data availability from a current-price page.

20. Do not circumvent authentication, CAPTCHAs, access controls, anti-bot protections, or explicit rate limits.

---

# 3. Entity Identity

21. Never use company name alone as the canonical security identifier.

22. Issuer and security must remain separate concepts.

23. Common and preferred shares must remain separate securities.

24. Never assume securities issued by the same company have identical economics.

25. Never infer share-class rights from ticker suffixes alone.

26. Historical tickers, ISINs, and legal names must be preserved where relevant.

27. Security mappings must not rely solely on fuzzy-name similarity.

28. Ambiguous entity matches must be flagged for review.

---

# 4. Share Rights

29. Voting rights, dividend rights, liquidation rights, conversion rights, and other security rights must be based on reliable evidence.

30. Preferred-share economics must not be guessed.

31. If important share rights cannot be verified, confidence must be reduced.

32. If unknown security rights materially affect valuation, the model must be allowed to return:

   `VALUATION INSUFFICIENT`

---

# 5. Financial Statements

33. Never mix consolidated and standalone financial statements without explicitly identifying the reporting perimeter.

34. Never silently combine IFRS and local-standard financial data.

35. Audited and unaudited reports must remain distinguishable.

36. Reporting period and publication date must remain separate fields.

37. Reported, derived, and estimated financial values must remain distinguishable.

38. Never use overlapping reporting periods incorrectly when calculating TTM values.

39. Original units and currencies must be preserved before normalization.

40. Unit conversions must be explicit and reproducible.

41. Inconsistent units must be detected and flagged.

42. Financial statement identities should be validated where possible.

43. Material reconciliation failures must be investigated rather than ignored.

---

# 6. Restatements

44. Never overwrite an original financial filing when a restatement is released.

45. Preserve both original and restated reports.

46. Preserve their respective publication dates.

47. Current research may use the latest valid restatement where appropriate.

48. Historical backtests may only use the financial information actually available at the historical date.

---

# 7. OCR and LLM Extraction

49. Prefer deterministic structured extraction over OCR or LLM extraction.

50. OCR should only be used when better extraction methods are unavailable.

51. LLMs may assist with:

   - document classification
   - label mapping
   - summarization
   - qualitative analysis
   - event classification

52. LLMs must not be treated as the numerical source of truth.

53. LLM-generated numeric values must not overwrite verified structured data without validation.

54. Low-confidence extraction must be flagged.

55. If a number cannot be reliably extracted, leave it missing.

---

# 8. Market Prices

56. Never assume the last traded price is currently executable.

57. A quoted price must remain distinguishable from an executable market price.

58. A day with no transaction must not automatically be treated as a genuine zero-return day.

59. Do not forward-fill prices and then pretend a trade occurred.

60. Stale prices must be explicitly flagged.

61. Large price changes caused by very few transactions must be flagged.

62. Market prices should retain timestamp/date information where available.

---

# 9. Price Series

63. Maintain separately where applicable:

   - raw observed prices
   - corporate-action-adjusted prices
   - total-return series

64. Never overwrite raw historical prices with adjusted values.

65. Corporate-action adjustments must only be applied after the corporate action has been verified.

66. Historical return calculations must account for relevant verified corporate actions.

---

# 10. Dividends

67. Dividend amounts must be tied to the correct security/share class.

68. Historical dividend calculations must use information available at the relevant time.

69. Backtests should include dividends when appropriate and reliably available.

70. Dividend yield must not be calculated from mismatched dates without explicit justification.

---

# 11. Ownership and Free Float

71. Never invent ownership percentages.

72. Never infer free float without supporting evidence.

73. Unknown free float must remain unknown rather than becoming an estimate unless explicitly modeled as an estimate.

74. Ownership information should be point-in-time where possible.

75. Ownership concentration must be considered when evaluating liquidity.

---

# 12. Valuation

76. Never apply the same valuation framework blindly to every sector.

77. Banks must use bank-appropriate valuation methods.

78. Insurance companies must use insurance-appropriate valuation methods.

79. Industrial companies may use DCF and enterprise-value methods where appropriate.

80. Commodity companies should incorporate economically relevant commodity assumptions where appropriate.

81. Fair value should normally be represented as a range rather than false precision.

82. Bear, Base, and Bull scenarios should be used where appropriate.

83. Important valuation assumptions must be explicit.

84. Valuation confidence must decline when financial or market data quality is poor.

85. If a credible valuation cannot be produced, return:

   `VALUATION INSUFFICIENT`

---

# 13. Valuation Consistency

86. Never mix real cash flows with nominal discount rates.

87. Never mix currencies without explicit FX conversion.

88. UZS and USD assumptions must not be silently combined.

89. FX conversion must retain the FX rate, date, and source where material.

90. Inflation assumptions, discount rates, and terminal-growth assumptions must be internally consistent.

91. Country-risk assumptions must be explicit rather than hidden.

---

# 14. Liquidity

92. Liquidity is a core component of investment analysis.

93. Never assume unlimited market liquidity.

94. Never assume a large position can be purchased at the displayed last price.

95. Never assume a large position can be liquidated at the displayed last price.

96. Position size must be analyzed relative to actual trading activity.

97. Trading frequency must be considered.

98. Zero-trade days must be considered.

99. Price staleness must be considered.

100. Bid/ask spread should be considered where available.

101. Free float should be considered where reliable.

102. Ownership concentration should be considered.

103. Estimated liquidation time should be calculated where possible.

104. Slippage must be considered when meaningful.

105. Liquidity estimates must expose uncertainty where market-depth information is unavailable.

---

# 15. Liquidity Risk Gates

106. Hard liquidity failures may override attractive fundamental valuation.

107. A fundamentally attractive security may still receive:

   `LIQUIDITY TRAP`

108. A security with an unreliable last price must not receive a normal high-confidence momentum signal.

109. An apparently large historical return must not automatically be interpreted as realistically achievable.

110. Realizable return is more important than theoretical mark-to-market return.

---

# 16. Factors and Scores

111. Raw financial or market metrics must remain distinguishable from transformed factor scores.

112. Do not manipulate raw source data through winsorization.

113. Analytical transformations must be documented.

114. Cross-sectional percentile scores should not be used when the peer group is too small to be meaningful.

115. Sector-dependent ratios must use sector-appropriate comparisons.

116. Missing critical data must not automatically produce an average score.

117. Factor weights must remain configurable.

118. Factor weights must not be optimized solely to maximize historical performance.

119. Statistical performance alone does not prove economic validity.

---

# 17. Attractiveness and Confidence

120. Investment attractiveness and confidence must remain separate.

121. A high attractiveness score does not imply high confidence.

122. Confidence should reflect factors such as:

   - data quality
   - reporting history
   - liquidity evidence
   - ownership transparency
   - share-right certainty
   - model stability

123. Low-confidence securities should not receive aggressive high-conviction recommendations solely because estimated upside is large.

---

# 18. Corporate Events and Anomalies

124. Corporate events must retain publication dates.

125. Historical models may only use an event after it became public.

126. An anomaly is an investigation trigger, not automatically a trading signal.

127. A positive corporate event does not automatically imply a BUY signal.

128. A negative event does not automatically imply a SELL signal.

129. Event materiality and confidence should remain separate.

---

# 19. Macroeconomic Data

130. Historical macro models may only use macro information after its actual release date.

131. Revised future macro data must not silently replace historically available data in backtests.

132. Macroeconomic context should not independently create stock recommendations.

133. Company macro sensitivities must have defensible economic reasoning.

---

# 20. Backtesting

134. No look-ahead bias.

135. No future financial reports.

136. No future ownership information.

137. No future corporate events.

138. No future macro releases.

139. No future corporate-action knowledge.

140. Use only information available at each historical decision point.

141. Do not assume instantaneous fills when historical liquidity would not support them.

142. Model transaction costs where applicable.

143. Model reasonable slippage where applicable.

144. Model partial and multi-day fills where necessary.

145. Do not assume unlimited participation in daily volume.

146. Include relevant dividends and verified corporate actions.

147. Delisted or failed securities must not be silently removed from historical universes.

148. Survivorship bias should be minimized wherever data permits.

149. Historical model performance must be distinguished from realistically executable historical performance.

---

# 21. Statistical Validation

150. Training and out-of-sample testing must remain separate.

151. Walk-forward validation should be preferred where appropriate.

152. Do not repeatedly tune models against the same out-of-sample period.

153. Record materially different strategy variants tested where practical.

154. Do not present only the best-performing model while hiding extensive failed experimentation.

155. Robustness should be tested against reasonable changes in:

   - transaction costs
   - slippage
   - execution delay
   - valuation assumptions
   - factor weights
   - holding periods

156. If model performance collapses under modest assumption changes, classify it as fragile.

---

# 22. Position Sizing and Execution

157. Position sizing must consider liquidity.

158. Position sizing must consider confidence.

159. Position sizing must consider governance and data quality.

160. Position sizing must consider portfolio concentration.

161. Intraday timing should not be presented as reliable without sufficient intraday evidence.

162. Do not fabricate precise execution timing.

163. If intraday timing cannot be supported, return:

   `INTRADAY TIMING NOT RELIABLE`

164. Initial versions of UZQUANT must not automatically execute live trades.

---

# 23. Model Versioning

165. Every investment signal must identify the model version that generated it.

166. Material scoring-model changes must create a new model version.

167. Material valuation-model changes must create a new model version.

168. Material liquidity-model changes must create a new model version.

169. Signals should preserve the relevant data snapshot or equivalent point-in-time reference.

170. Never silently rewrite historical model signals using a newer model.

171. Corrections must remain distinguishable from the originally generated signal.

---

# 24. Data Pipeline Health

172. Automated data pipelines must record their last successful update time.

173. Pipeline failures must not be silently ignored.

174. If a critical source becomes stale or unavailable, affected analytical outputs must be marked accordingly.

175. The platform must not display stale analysis as if it were freshly updated.

---

# 25. Research Outputs

176. Every material investment recommendation must be explainable.

177. The system should explain:

   - why the security appears attractive or unattractive
   - valuation assumptions
   - liquidity
   - risks
   - catalysts
   - confidence
   - missing data
   - triggered risk gates
   - what could invalidate the thesis

178. Automated narrative research must be grounded in structured model outputs or source documents.

179. LLM-generated research must not introduce unsupported factual claims.

---

# 26. Paper Trading

180. Paper-trading signals must be timestamped when generated.

181. Paper signals must not be retroactively altered after future performance becomes known.

182. Simulated execution should use the same liquidity assumptions intended for real-world use.

183. Paper trading should evaluate both investment signals and execution assumptions.

---

# 27. Safety and Market Conduct

184. Do not use non-public insider information.

185. Do not design market-manipulation strategies.

186. Do not design pump-and-dump systems.

187. Do not attempt to artificially move illiquid securities.

188. Use only legitimate public or authorized data.

---

# 28. Final Principles

When accuracy conflicts with completeness:

**Choose accuracy.**

When attractive theoretical return conflicts with liquidity:

**Choose realizable return.**

When model complexity conflicts with transparency:

**Choose transparency.**

When historical performance conflicts with realistic execution:

**Choose realistic execution.**

When evidence is weak:

**Reduce confidence.**

When critical information is unavailable:

**Return DATA INSUFFICIENT.**

UZQUANT should fail safely rather than confidently produce an unreliable investment recommendation.
