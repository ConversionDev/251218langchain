import type { RecruitStatus } from "@/modules/shared/types";

export const NEW_HIRE_STATUS_LABELS: Record<RecruitStatus, string> = {
  pending: "미검토",
  screening: "심사 중",
  hired: "합격",
  rejected: "탈락",
};

export const NEW_HIRES_MESSAGES = {
  header: {
    flow: "이력서 업로드 → AI 분석 → 등록",
    title: "신입 관리",
    descriptionPrefix: "이력서를 업로드하면 AI가 기본 정보와 Success DNA를 채웁니다. 확인 후 등록하면 이 페이지의",
    descriptionEmphasis: "신입 목록",
    descriptionSuffix: "에 추가됩니다. 기존 직원은",
    existingEmployeesLinkLabel: "기존 직원",
    descriptionTail: "에서 관리하세요.",
  },
  kpi: {
    totalApplicants: "총 지원자",
    screening: "심사 중",
    hired: "합격",
    rejected: "탈락",
  },
  toast: {
    analyzeSuccess: (name: string) => `${name}님 AI 분석 완료. Success DNA가 저장되었습니다.`,
    analyzeFailed: "AI 분석에 실패했습니다.",
    statusUpdated: (name: string, status: RecruitStatus) =>
      `${name}님 상태가 ${NEW_HIRE_STATUS_LABELS[status]}(으)로 변경되었습니다.`,
    statusUpdateFailed: "상태 변경에 실패했습니다.",
    reasonSaved: "평가 근거가 저장되었습니다.",
    saveFailed: "저장에 실패했습니다.",
    infoUpdated: (name: string) => `${name} 정보가 수정되었습니다.`,
    duplicateResume: (name: string) =>
      `동일한 이력서가 이미 등록되어 있습니다 (${name}). DB에 추가하지 않았습니다.`,
    createFailed: "등록에 실패했습니다.",
    deleted: (name: string) => `${name} 데이터가 삭제되었습니다.`,
    deleteFailed: "삭제에 실패했습니다.",
    onboarded: (name: string) => `${name}님이 기존 직원으로 전환되었습니다.`,
    onboardFailed: "입사 확정 처리에 실패했습니다.",
  },
  confirm: {
    deleteApplicant: (name: string) => `${name} 지원자 데이터를 삭제할까요?`,
    onboardApplicant: (name: string) => `${name}님을 입사 확정 처리하고 기존 직원으로 전환할까요?`,
  },
  section: {
    registerTitle: "이력서로 신입 등록",
    registerDescription: "PDF/Word/HWP 업로드 시 기본 정보와 역량 분석이 자동으로 채워집니다.",
    registerButton: "이력서 업로드하여 등록하기",
    registerDoneHint: "등록 완료. 아래 목록에서 확인하세요.",
    atsTitle: "지원자 · 신입 목록 (ATS)",
    atsDescription: "이름/부서로 필터링하고 상태별로 심사 진행을 관리하세요.",
    totalLabel: (total: number) => `신입 전체 ${total}명`,
    refresh: "새로고침",
    loading: "로딩 중…",
    empty: "해당 상태의 지원자가 없습니다.",
    emptyListLead: "지원자가 없습니다. JSONL 적재 후",
    emptyListRefresh: "새로고침",
    emptyListTail: "을 누르거나, 위에서 이력서 업로드로 등록하세요.",
    emptyListHint: "(적재한 DB와 프론트가 같은 API를 쓰는지 확인하세요.)",
    footerGuide:
      "미검토: 이력서 접수만 된 상태. [AI 분석]으로 엑사원이 Success DNA를 생성합니다. 심사 중에서 [합격]/[탈락]으로 결정하세요.",
  },
  table: {
    headers: {
      name: "이름",
      department: "부서",
      jobTitle: "직급",
      applicationDate: "지원일",
      status: "상태",
      rejectionReason: "탈락 사유",
      actions: "액션",
    },
    nameTitle: "이 직원을 Intelligence에서 조회",
  },
  tabs: {
    pending: "미검토",
    screening: "심사 중",
    hired: "합격",
    rejected: "탈락",
  },
  buttons: {
    analyze: "AI 분석",
    analyzeAgain: "AI 재분석",
    analyzing: "분석 중…",
    analyzedDone: "분석 완료",
    screening: "심사중",
    hired: "합격",
    rejected: "탈락",
    onboard: "입사확정",
    edit: "수정",
    delete: "삭제",
    cancel: "취소",
    save: "저장",
    saving: "저장 중…",
    rejectProcessing: "처리 중…",
    rejectConfirm: "탈락 처리",
  },
  dialogs: {
    reasonTitle: (name: string) => `${name} · 평가 근거 (수동 수정 가능)`,
    reasonDnaLabel: "Success DNA",
    rejectTitle: (name: string) => `${name} · 탈락 사유`,
    rejectDescription: "탈락 처리 시 사유를 입력하면 이의 제기·감사 대응 시 참고할 수 있습니다. (선택)",
  },
  input: {
    searchPlaceholder: "검색...",
    reasonPlaceholder: "AI가 생성한 평가 근거를 확인·수정하세요.",
    rejectionPlaceholder: "예: 경력 부합도 낮음, 자격 요건 미충족 등",
  },
};

export const EMPLOYEE_FORM_MESSAGES = {
  dialog: {
    editTitle: "직원 수정",
    createTitle: "직원 등록",
    saveButton: "저장",
    createButton: "등록",
  },
  upload: {
    uploadLegend: "이력서 업로드",
    resumeLegend: "이력서",
    acceptedHint: "PDF, TXT, Word(.docx), HWP(.hwp) · 업로드 시 빈칸에 정보가 채워집니다. 등록은 등록 버튼을 눌러 주세요.",
    editReplaceHint: "새 이력서로 갱신 (빈칸 채움 후 저장 버튼)",
    editUploadHint: "이력서 업로드 (빈칸 채움 후 저장 버튼)",
    existingResumeSummary: (eduCount: number, expCount: number) =>
      `등록된 이력서가 반영되어 있습니다 (학력 ${eduCount}건, 경력 ${expCount}건). 새 파일을 올리면 덮어씁니다.`,
    noResumeSummary: "등록된 이력서가 없습니다. 새 파일을 올리면 분석 후 반영됩니다.",
    departmentFallbackKeyword: "명시 불가",
    departmentFallbackValue: "미정",
    cachedLoaded: "저장된 분석 결과를 불러왔습니다. 내용 확인 후 등록 버튼을 눌러 주세요.",
    analyzed: "이력서를 분석했습니다. 내용을 확인한 뒤 등록 버튼을 눌러 주세요.",
    failed: "이력서 처리에 실패했습니다.",
    phaseUploading: "파일 확인 중…",
    phaseExtracting: "텍스트 추출 중…",
    phaseAnalyzing: "AI가 이력서를 분석하고 있습니다…",
    dropzoneIdle: "이력서를 놓거나 클릭해 업로드",
  },
  form: {
    legend: "기본 정보",
    labels: {
      name: "이름",
      jobTitle: "직급",
      department: "부서",
      email: "이메일",
      applicationDate: "지원일",
      joinedAt: "입사일",
    },
    cancel: "취소",
  },
  toast: {
    updated: "데이터 변경사항이 저장되었습니다. Credential 모듈에서 해시 갱신이 필요합니다.",
    created: "직원이 등록되었습니다.",
  },
};

export const CORE_EMPLOYEES_MESSAGES = {
  header: {
    flow: "등록된 직원 목록 · 수정/삭제",
    title: "기존 직원 관리",
    descriptionPrefix: "DB에 등록된 직원의 이력·공시 지표를 조회·수정합니다. 신입은",
    newHireLinkLabel: "신입 관리",
    descriptionTail: "에서 등록하세요.",
  },
  buttons: {
    backfill: "결측치 자동 보정",
    backfilling: "보정 중...",
    addEmployee: "직원 추가",
  },
  section: {
    listTitle: "직원 리스트",
    listDescription: "이름을 제외한 행 영역 또는 상세(문서) 버튼을 클릭하면 이력 상세가 열립니다. 수정/삭제는 행 내 버튼을 사용하세요.",
    totalLabel: (total: number) => `전체 ${total}명`,
    loading: "로딩 중…",
  },
  confirm: {
    deleteEmployee: "이 직원 데이터를 삭제할까요?",
    profileBackfill: (preview: {
      targetRegularEmployees: number;
      gender: number;
      age: number;
      trainingHours: number;
    }) =>
      [
        "결측치 보정 미리보기",
        `- 대상(기존 직원): ${preview.targetRegularEmployees}명`,
        `- 성별 보정 예정: ${preview.gender}명`,
        `- 나이 보정 예정: ${preview.age}명`,
        `- 교육시간 보정 예정: ${preview.trainingHours}명`,
        "",
        "실제로 DB에 저장할까요?",
      ].join("\n"),
    rowClickToIntelligence: (name: string) => `${name} 님을 선택했습니다. 역량 진단 페이지로 이동할까요?`,
  },
  toast: {
    analyzeSuccess: (name: string) => `${name} AI 분석이 완료되었습니다.`,
    analyzeFailed: "AI 분석에 실패했습니다.",
    saveFailed: "저장에 실패했습니다.",
    deleteFailed: "삭제에 실패했습니다.",
    backfillFailed: "결측 프로필 보정에 실패했습니다.",
    backfillCompleted: (updated: { gender: number; age: number; trainingHours: number }) =>
      `결측치 보정 완료: 성별 ${updated.gender}명, 나이 ${updated.age}명, 교육시간 ${updated.trainingHours}명`,
  },
};

export const EMPLOYEE_LIST_MESSAGES = {
  filter: {
    nameLabel: "이름",
    deptLabel: "부서",
    searchPlaceholder: "검색...",
  },
  table: {
    headers: {
      name: "이름",
      jobTitle: "직급",
      department: "부서",
      gender: "성별",
      age: "연령",
      employmentType: "고용형태",
      trainingHours: "교육시간",
      actions: "작업",
    },
    rowNameTitle: "이름 클릭은 선택만 됩니다. 이력 상세는 행의 다른 영역을 클릭하세요.",
    detailTitle: "이력 상세",
  },
  actions: {
    analyze: "AI 분석",
    analyzing: "분석 중…",
    detail: "상세",
    edit: "수정",
    delete: "삭제",
  },
};

export const APPLY_MESSAGES = {
  common: {
    cancel: "취소",
    add: "추가",
    remove: "삭제",
  },
  form: {
    defaultJobTitle: "인턴",
    departmentFallbackKeyword: "명시 불가",
    departmentFallbackValue: "미정",
    requiredFieldError: "이름, 이메일, 희망 부서를 입력해 주세요.",
    title: "이력서 지원",
    description: "아래 항목을 작성한 뒤 제출해 주세요. 검토 후 연락드리겠습니다.",
    basicInfoTitle: "기본 정보",
    nameLabel: "이름 *",
    namePlaceholder: "홍길동",
    emailLabel: "이메일 *",
    departmentLabel: "희망 부서 *",
    departmentPlaceholder: "예: 개발, 마케팅, 컨설팅",
    jobTitleLabel: "지원 직급",
    jobTitleIntern: "인턴",
    jobTitleStaff: "사원",
    genderLabel: "성별",
    genderUndisclosed: "미기입",
    genderMale: "남",
    genderFemale: "여",
    ageLabel: "만 나이 (선택)",
    agePlaceholder: "25",
  },
  toast: {
    cachedLoaded: "저장된 분석 결과를 불러왔습니다. 내용을 확인한 뒤 제출해 주세요.",
    duplicateResume: "이 이력서는 이미 등록되어 있어 제출할 수 없습니다. 다른 이력서를 업로드해 주세요.",
    analyzed: "이력서를 분석했습니다. 아래 항목을 확인한 뒤 제출해 주세요.",
    uploadFailed: "이력서 처리에 실패했습니다.",
    attachmentRemoved: "이력서 첨부를 해제했습니다.",
    submitted: "지원서가 접수되었습니다.",
    submitFailed: "제출에 실패했습니다.",
  },
  upload: {
    phaseUploading: "파일 확인 중…",
    phaseExtracting: "텍스트 추출 중…",
    phaseAnalyzing: "AI가 이력서를 분석하고 있습니다…",
    switchResume: "다른 이력서로 바꾸기 (클릭 또는 끌어오기)",
    idle: "이력서를 놓거나 클릭해 업로드",
  },
  page: {
    submittedTitle: "지원이 완료되었습니다",
    submittedDescription: "입력하신 내용이 정상적으로 접수되었습니다. 검토 후 연락드리겠습니다.",
    backToMain: "메인으로 돌아가기",
    toMain: "메인으로",
  },
  uploadSection: {
    title: "이력서 업로드 (선택)",
    description: "이력서를 업로드하면 기본 정보·학력·경력이 자동으로 채워집니다. 다른 화면으로 이동해도 복원됩니다.",
    attachedPrefix: "첨부됨:",
    removeAriaLabel: "이력서 첨부 해제",
    removeButton: "제거",
    autofilledHint: "아래 빈칸이 자동으로 채워졌습니다. 수정 후 제출해 주세요. 다른 파일로 바꾸려면 아래에 다시 올려 주세요.",
  },
  educationSection: {
    title: "학력",
    itemLabel: (index: number) => `학력 ${index + 1}`,
    schoolLabel: "학교명",
    schoolPlaceholder: "OO대학교",
    degreeLabel: "학위 / 전공",
    degreePlaceholder: "예: 컴퓨터공학 학사",
    graduationLabel: "졸업일 (YYYY-MM)",
  },
  experienceSection: {
    title: "경력 / 활동 (선택)",
    itemLabel: (index: number) => `경력 ${index + 1}`,
    companyLabel: "회사 / 단체명",
    companyPlaceholder: "예: 스타트업, 동아리",
    roleLabel: "역할",
    rolePlaceholder: "예: 인턴, 팀장",
    startDateLabel: "시작일 (YYYY-MM)",
    endDateLabel: "종료일 (YYYY-MM)",
    endDatePlaceholder: "재직 중",
    descriptionLabel: "업무 설명 (선택)",
    descriptionPlaceholder: "담당 업무 요약",
  },
  submitButton: {
    submitting: "제출 중...",
    blockedDuplicate: "제출 불가 (중복 이력서)",
    submit: "지원서 제출",
  },
  duplicateBlockNotice:
    "이 이력서는 이미 등록되어 있어 제출할 수 없습니다. 다른 이력서를 업로드하거나 첨부를 제거한 뒤 수동으로 작성해 주세요.",
};
