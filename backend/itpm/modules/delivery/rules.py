KINDS={'materials':'资料请求','baseline':'范围确认','verification':'业务验证'}
OUTCOMES={'provided':'已提供资料','confirmed':'确认范围','passed':'验证通过','changes':'需要修改'}
FEEDBACK_TYPES={'original_gap':'原验收标准未达标 / 问题修复','improvement':'现有功能优化','new_feature':'新增功能或扩大范围','requirement_change':'业务目标或需求重构','other':'其他，需要 IT 判断'}
FEEDBACK_ROUTES={'same_l3_rework':'当前 L3 整改','same_l3_improvement':'当前 L3 优化事项','new_l3_feature':'新建功能 L3','new_l3_restructure':'新建需求重构 L3','it_review':'待 IT 判断'}
DEFAULT_ROUTES=dict(zip(FEEDBACK_TYPES,FEEDBACK_ROUTES))
