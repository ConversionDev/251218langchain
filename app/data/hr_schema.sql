-- ============================================================================
-- HR 시스템 DDL (직원, 부서, 배치)
-- ============================================================================
-- 생성일: 2026-01-21
-- 설명: Employee, Department, Placement 테이블 생성 스크립트
-- ============================================================================

-- 1. Employees 테이블 (직원)
-- ============================================================================
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    employee_number VARCHAR(50) UNIQUE NOT NULL,  -- 사원번호 (고유)
    name VARCHAR(100) NOT NULL,                   -- 이름
    email VARCHAR(255) UNIQUE NOT NULL,           -- 이메일 (고유)
    phone VARCHAR(20),                            -- 전화번호
    position VARCHAR(100),                        -- 직급/직책
    hire_date DATE,                               -- 입사일
    is_active BOOLEAN DEFAULT TRUE NOT NULL,     -- 재직 여부
    notes TEXT,                                   -- 비고/메모
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,  -- 생성 일시
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL  -- 수정 일시
);

-- 인덱스 생성
CREATE INDEX idx_employees_employee_number ON employees(employee_number);
CREATE INDEX idx_employees_email ON employees(email);
CREATE INDEX idx_employees_is_active ON employees(is_active);
CREATE INDEX idx_employees_hire_date ON employees(hire_date);

-- 코멘트 추가
COMMENT ON TABLE employees IS '직원 정보를 관리하는 테이블';
COMMENT ON COLUMN employees.id IS '직원 ID (자동 증가)';
COMMENT ON COLUMN employees.employee_number IS '사원번호 (고유)';
COMMENT ON COLUMN employees.name IS '이름';
COMMENT ON COLUMN employees.email IS '이메일 (고유)';
COMMENT ON COLUMN employees.phone IS '전화번호';
COMMENT ON COLUMN employees.position IS '직급/직책';
COMMENT ON COLUMN employees.hire_date IS '입사일';
COMMENT ON COLUMN employees.is_active IS '재직 여부';
COMMENT ON COLUMN employees.notes IS '비고/메모';
COMMENT ON COLUMN employees.created_at IS '생성 일시';
COMMENT ON COLUMN employees.updated_at IS '수정 일시';

-- updated_at 자동 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_employees_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION update_employees_updated_at();


-- 2. Departments 테이블 (부서)
-- ============================================================================
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,            -- 부서 코드 (고유)
    name VARCHAR(100) NOT NULL,                   -- 부서명
    description TEXT,                            -- 부서 설명
    parent_department_id INTEGER,                 -- 상위 부서 ID (계층 구조)
    manager_id INTEGER,                           -- 부서장 직원 ID
    is_active BOOLEAN DEFAULT TRUE NOT NULL,     -- 활성화 여부
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,  -- 생성 일시
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,  -- 수정 일시

    -- 외래키 제약조건
    CONSTRAINT fk_departments_parent
        FOREIGN KEY (parent_department_id)
        REFERENCES departments(id)
        ON DELETE SET NULL,
    CONSTRAINT fk_departments_manager
        FOREIGN KEY (manager_id)
        REFERENCES employees(id)
        ON DELETE SET NULL
);

-- 인덱스 생성
CREATE INDEX idx_departments_code ON departments(code);
CREATE INDEX idx_departments_parent ON departments(parent_department_id);
CREATE INDEX idx_departments_manager ON departments(manager_id);
CREATE INDEX idx_departments_is_active ON departments(is_active);

-- 코멘트 추가
COMMENT ON TABLE departments IS '부서 정보를 관리하는 테이블';
COMMENT ON COLUMN departments.id IS '부서 ID (자동 증가)';
COMMENT ON COLUMN departments.code IS '부서 코드 (고유)';
COMMENT ON COLUMN departments.name IS '부서명';
COMMENT ON COLUMN departments.description IS '부서 설명';
COMMENT ON COLUMN departments.parent_department_id IS '상위 부서 ID (계층 구조)';
COMMENT ON COLUMN departments.manager_id IS '부서장 직원 ID';
COMMENT ON COLUMN departments.is_active IS '활성화 여부';
COMMENT ON COLUMN departments.created_at IS '생성 일시';
COMMENT ON COLUMN departments.updated_at IS '수정 일시';

-- updated_at 자동 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_departments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_departments_updated_at
    BEFORE UPDATE ON departments
    FOR EACH ROW
    EXECUTE FUNCTION update_departments_updated_at();


-- 3. Placements 테이블 (배치) - 교차 엔티티
-- ============================================================================
CREATE TABLE placements (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,                 -- 직원 ID
    department_id INTEGER NOT NULL,               -- 부서 ID
    position VARCHAR(100),                         -- 배치 직급/직책
    start_date DATE NOT NULL,                     -- 배치 시작일
    end_date DATE,                                -- 배치 종료일 (NULL이면 현재 배치)
    is_active BOOLEAN DEFAULT TRUE NOT NULL,     -- 활성 배치 여부
    notes VARCHAR(500),                           -- 비고/메모
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,  -- 생성 일시
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,  -- 수정 일시

    -- 외래키 제약조건
    CONSTRAINT fk_placements_employee
        FOREIGN KEY (employee_id)
        REFERENCES employees(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_placements_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id)
        ON DELETE CASCADE,

    -- 체크 제약조건
    CONSTRAINT check_end_date_after_start
        CHECK (end_date IS NULL OR end_date >= start_date)
);

-- 인덱스 생성
CREATE INDEX idx_placements_employee ON placements(employee_id);
CREATE INDEX idx_placements_department ON placements(department_id);
CREATE INDEX idx_placements_start_date ON placements(start_date);
CREATE INDEX idx_placements_end_date ON placements(end_date);
CREATE INDEX idx_placements_is_active ON placements(is_active);
CREATE INDEX idx_placements_employee_department ON placements(employee_id, department_id);

-- 코멘트 추가
COMMENT ON TABLE placements IS 'Employee와 Department를 연결하는 교차 엔티티 - 직원의 부서 배치 정보를 관리';
COMMENT ON COLUMN placements.id IS '배치 ID (자동 증가)';
COMMENT ON COLUMN placements.employee_id IS '직원 ID';
COMMENT ON COLUMN placements.department_id IS '부서 ID';
COMMENT ON COLUMN placements.position IS '배치 직급/직책';
COMMENT ON COLUMN placements.start_date IS '배치 시작일';
COMMENT ON COLUMN placements.end_date IS '배치 종료일 (NULL이면 현재 배치)';
COMMENT ON COLUMN placements.is_active IS '활성 배치 여부';
COMMENT ON COLUMN placements.notes IS '비고/메모';
COMMENT ON COLUMN placements.created_at IS '생성 일시';
COMMENT ON COLUMN placements.updated_at IS '수정 일시';

-- updated_at 자동 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_placements_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_placements_updated_at
    BEFORE UPDATE ON placements
    FOR EACH ROW
    EXECUTE FUNCTION update_placements_updated_at();


-- ============================================================================
-- 스키마 생성 완료
-- ============================================================================
