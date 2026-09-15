# AgroSmart Artifacts

This folder contains the validated artifacts for the AgroSmart SIH project.

## Contents

### model1/
EfficientNet-B0 disease/pest classifier.

Files:
- agrosmart_model1_efficientnet_b0.pth
- model_config.json

### knowledge_base/
Validated treatment knowledge base.

File:
- MASTER_TREATMENT_KNOWLEDGE_BASE_V2.json

### model2/deployment_package_v1/
Frozen epidemiological forecasting and case-impact engine.

Important:
- Do not rewrite scientific logic.
- Do not convert suitability outputs into disease probabilities.
- Do not produce personalized yield-loss percentages.
- Cotton bollworm remains generic until species confirmation.
- Healthy classes must route to PREVENTION_ONLY.
- Treatment actions must use the knowledge base and officer-validation workflow.

These artifact folders should be treated as read-only.
Application code should wrap and call them rather than modifying their scientific contents.
