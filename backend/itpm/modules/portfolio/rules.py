from itpm.core.errors import require

def solution_type(value,vocabulary):
    v=str(value or '').strip();v=vocabulary['PROJECT_SOLUTION_TYPE_MAP'].get(v,v)
    return v if v in {x['key'] for x in vocabulary['PROJECT_SOLUTION_TYPES']} else 'unknown'

def validate_project(data,creating=False):
    if creating:require(data.get('name'),'name required')
    for field,label in [('department','部门'),('devOwner','开发负责人'),('targetEndDate','目标结束时间')]:
        require(data.get(field),label+'必填')
