-- 智诊通系统用户管理扩展脚本
-- 添加就诊人管理和精准检索支持

-- 1. 扩展用户表，添加身份证号和手机号字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS id_card VARCHAR(18);
ALTER TABLE users ADD COLUMN IF NOT EXISTS real_phone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS user_unique_id VARCHAR(50) UNIQUE;

-- 为现有用户生成唯一ID
UPDATE users SET user_unique_id = 'USER_' || id::text WHERE user_unique_id IS NULL;

-- 2. 创建就诊人表
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_unique_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    id_card VARCHAR(18),
    phone VARCHAR(20),
    age INTEGER,
    gender VARCHAR(10),
    relationship VARCHAR(20) DEFAULT 'self', -- self, spouse, child, parent, other
    medical_history TEXT,
    allergies TEXT,
    medications TEXT,
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. 创建用户-就诊人关联表（支持一个用户管理多个就诊人）
CREATE TABLE IF NOT EXISTS user_patient_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    relation_type VARCHAR(20) DEFAULT 'owner', -- owner, guardian, family
    permissions JSONB DEFAULT '{"view": true, "edit": true, "delete": false}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, patient_id)
);

-- 4. 创建医疗记录表（存储到ES的数据结构）
CREATE TABLE IF NOT EXISTS medical_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_unique_id VARCHAR(50) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    record_type VARCHAR(20) DEFAULT 'visit', -- visit, diagnosis, treatment, prescription
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    department VARCHAR(100),
    doctor VARCHAR(100),
    visit_date TIMESTAMP WITH TIME ZONE,
    symptoms TEXT,
    diagnosis TEXT,
    treatment TEXT,
    medications TEXT,
    notes TEXT,
    attachments JSONB DEFAULT '[]',
    is_synced_to_es BOOLEAN DEFAULT FALSE,
    es_document_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. 创建索引
CREATE INDEX IF NOT EXISTS idx_users_user_unique_id ON users(user_unique_id);
CREATE INDEX IF NOT EXISTS idx_users_id_card ON users(id_card);
CREATE INDEX IF NOT EXISTS idx_users_real_phone ON users(real_phone);

CREATE INDEX IF NOT EXISTS idx_patients_user_id ON patients(user_id);
CREATE INDEX IF NOT EXISTS idx_patients_patient_unique_id ON patients(patient_unique_id);
CREATE INDEX IF NOT EXISTS idx_patients_id_card ON patients(id_card);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);

CREATE INDEX IF NOT EXISTS idx_user_patient_relations_user_id ON user_patient_relations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_patient_relations_patient_id ON user_patient_relations(patient_id);

CREATE INDEX IF NOT EXISTS idx_medical_records_patient_unique_id ON medical_records(patient_unique_id);
CREATE INDEX IF NOT EXISTS idx_medical_records_user_id ON medical_records(user_id);
CREATE INDEX IF NOT EXISTS idx_medical_records_visit_date ON medical_records(visit_date);
CREATE INDEX IF NOT EXISTS idx_medical_records_is_synced_to_es ON medical_records(is_synced_to_es);

-- 6. 创建触发器，自动生成唯一ID
CREATE OR REPLACE FUNCTION generate_patient_unique_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.patient_unique_id IS NULL THEN
        NEW.patient_unique_id := 'PATIENT_' || NEW.id::text;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_generate_patient_unique_id
    BEFORE INSERT ON patients
    FOR EACH ROW
    EXECUTE FUNCTION generate_patient_unique_id();

-- 7. 创建视图：用户可访问的就诊人列表
CREATE OR REPLACE VIEW user_accessible_patients AS
SELECT 
    p.*,
    u.username as owner_username,
    upr.relation_type,
    upr.permissions
FROM patients p
JOIN user_patient_relations upr ON p.id = upr.patient_id
JOIN users u ON upr.user_id = u.id
WHERE p.is_active = TRUE;

-- 8. 创建函数：获取用户的所有就诊人ID
CREATE OR REPLACE FUNCTION get_user_patient_ids(p_user_id UUID)
RETURNS TABLE(patient_unique_id VARCHAR(50)) AS $$
BEGIN
    RETURN QUERY
    SELECT p.patient_unique_id
    FROM patients p
    JOIN user_patient_relations upr ON p.id = upr.patient_id
    WHERE upr.user_id = p_user_id AND p.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- 9. 插入示例数据
INSERT INTO patients (user_id, name, id_card, phone, age, gender, relationship, medical_history)
SELECT 
    u.id,
    '张三',
    '110101199001011234',
    '13800138000',
    34,
    '男',
    'self',
    '高血压病史3年，定期服药'
FROM users u 
WHERE u.username = 'admin'
LIMIT 1;

-- 为示例用户创建关联关系
INSERT INTO user_patient_relations (user_id, patient_id, relation_type)
SELECT 
    u.id,
    p.id,
    'owner'
FROM users u, patients p
WHERE u.username = 'admin' AND p.name = '张三'
LIMIT 1;
