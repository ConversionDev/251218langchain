"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import {
  getEditableInitialData,
  type EditableResumeData,
  type EditableExperience,
  type EditableEducation,
  type EditableProject,
  type EditableSkillGroup,
} from "./resumeData";

const resumeStyles = {
  fontFamily: "'Noto Sans KR', -apple-system, sans-serif",
  fontSize: "10.5pt",
  lineHeight: 1.55,
  color: "#222",
  maxWidth: "210mm",
  margin: "0 auto",
  padding: "18mm 20mm",
  background: "#fff",
};

/** contentEditable 단일 라인: 포커스 중에는 state 덮어쓰지 않음, blur 시 반영 */
function EditableSpan({
  id,
  focusedField,
  setFocusedField,
  value,
  onBlur,
  className,
  style,
}: {
  id: string;
  focusedField: string | null;
  setFocusedField: (v: string | null) => void;
  value: string;
  onBlur: (v: string) => void;
  className?: string;
  style?: React.CSSProperties;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (ref.current && focusedField !== id) ref.current.textContent = value;
  }, [value, focusedField, id]);
  return (
    <span
      ref={ref}
      contentEditable
      suppressContentEditableWarning
      className={className}
      style={style}
      onFocus={() => setFocusedField(id)}
      onBlur={(e) => {
        onBlur((e.currentTarget.textContent ?? "").trim());
        setFocusedField(null);
      }}
    />
  );
}

/** contentEditable 블록(여러 줄): intro 등 */
function EditableBlock({
  id,
  focusedField,
  setFocusedField,
  value,
  onBlur,
  className,
  style,
}: {
  id: string;
  focusedField: string | null;
  setFocusedField: (v: string | null) => void;
  value: string;
  onBlur: (v: string) => void;
  className?: string;
  style?: React.CSSProperties;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current && focusedField !== id) ref.current.textContent = value;
  }, [value, focusedField, id]);
  return (
    <div
      ref={ref}
      contentEditable
      suppressContentEditableWarning
      className={className}
      style={style}
      onFocus={() => setFocusedField(id)}
      onBlur={(e) => {
        onBlur((e.currentTarget.textContent ?? "").trim());
        setFocusedField(null);
      }}
    />
  );
}

/** 리스트 한 줄 편집 (블릿/수상 등) — HTML 양식처럼 · 불릿 */
function EditableLi({
  id,
  focusedField,
  setFocusedField,
  value,
  onBlur,
}: {
  id: string;
  focusedField: string | null;
  setFocusedField: (v: string | null) => void;
  value: string;
  onBlur: (v: string) => void;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (ref.current && focusedField !== id) ref.current.textContent = value;
  }, [value, focusedField, id]);
  return (
    <li
      style={{
        position: "relative",
        paddingLeft: "14px",
        marginBottom: "3px",
        fontSize: "10pt",
        color: "#333",
        listStyle: "none",
      }}
    >
      <span
        style={{
          position: "absolute",
          left: 0,
          fontWeight: 700,
          color: "#888",
        }}
      >
        ·
      </span>
      <span
        ref={ref}
        contentEditable
        suppressContentEditableWarning
        className="outline-none min-w-[1ch]"
        onFocus={() => setFocusedField(id)}
        onBlur={(e) => {
          onBlur((e.currentTarget.textContent ?? "").trim());
          setFocusedField(null);
        }}
      />
    </li>
  );
}

export function ResumeView() {
  const [data, setData] = useState<EditableResumeData>(getEditableInitialData);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const setBasic = useCallback((key: keyof EditableResumeData["basic"], value: string) => {
    setData((prev) => ({ ...prev, basic: { ...prev.basic, [key]: value } }));
  }, []);

  const setIntro = useCallback((value: string) => {
    setData((prev) => ({ ...prev, intro: value }));
  }, []);

  const setAwards = useCallback((index: number, value: string) => {
    setData((prev) => {
      const next = [...prev.awards];
      if (value === "" && next.length > 1) {
        next.splice(index, 1);
      } else {
        next[index] = value;
      }
      return { ...prev, awards: next };
    });
  }, []);

  const setExperience = useCallback((index: number, patch: Partial<EditableExperience>) => {
    setData((prev) => {
      const next = [...prev.experience];
      next[index] = { ...next[index], ...patch };
      return { ...prev, experience: next };
    });
  }, []);

  const setExperienceBullet = useCallback((expIndex: number, bulletIndex: number, value: string) => {
    setData((prev) => {
      const next = [...prev.experience];
      const bullets = [...next[expIndex].bullets];
      if (value === "" && bullets.length > 1) {
        bullets.splice(bulletIndex, 1);
      } else {
        bullets[bulletIndex] = value;
      }
      next[expIndex] = { ...next[expIndex], bullets };
      return { ...prev, experience: next };
    });
  }, []);

  const setEducation = useCallback((index: number, patch: Partial<EditableEducation>) => {
    setData((prev) => {
      const next = [...prev.education];
      next[index] = { ...next[index], ...patch };
      return { ...prev, education: next };
    });
  }, []);

  const setProject = useCallback((index: number, patch: Partial<EditableProject>) => {
    setData((prev) => {
      const next = [...prev.projects];
      next[index] = { ...next[index], ...patch };
      return { ...prev, projects: next };
    });
  }, []);

  const setSkillGroup = useCallback((groupIndex: number, patch: Partial<EditableSkillGroup>) => {
    setData((prev) => {
      const next = prev.skillGroups.map((g, i) =>
        i === groupIndex ? { ...g, ...patch } : g
      );
      return { ...prev, skillGroups: next };
    });
  }, []);

  const setSkillTag = useCallback((groupIndex: number, tagIndex: number, value: string) => {
    setData((prev) => {
      const next = prev.skillGroups.map((g, i) => {
        if (i !== groupIndex) return g;
        const tags = [...g.tags];
        if (value === "" && tags.length > 1) {
          tags.splice(tagIndex, 1);
        } else {
          tags[tagIndex] = value;
        }
        return { ...g, tags };
      });
      return { ...prev, skillGroups: next };
    });
  }, []);

  return (
    <div
      className="flex flex-col h-full overflow-auto print:overflow-visible text-left"
      style={resumeStyles}
    >
      {/* ===== 헤더 (HTML 양식) ===== */}
      <header
        style={{
          textAlign: "center",
          paddingBottom: "18px",
          marginBottom: "20px",
          borderBottom: "1.5px solid #333",
        }}
      >
        <h1
          style={{
            fontSize: "24pt",
            fontWeight: 700,
            letterSpacing: "-0.02em",
            color: "#111",
            marginBottom: "6px",
          }}
        >
          <EditableSpan
            id="basic.name"
            focusedField={focusedField}
            setFocusedField={setFocusedField}
            value={data.basic.name}
            onBlur={(v) => setBasic("name", v)}
            className="outline-none min-w-[1ch]"
          />
        </h1>
        <p
          style={{
            fontSize: "11pt",
            fontWeight: 500,
            color: "#555",
            marginBottom: "12px",
          }}
        >
          <EditableSpan
            id="basic.title"
            focusedField={focusedField}
            setFocusedField={setFocusedField}
            value={data.basic.title}
            onBlur={(v) => setBasic("title", v)}
            className="outline-none min-w-[1ch]"
          />
        </p>
        <p style={{ fontSize: "9.5pt", color: "#666" }}>
          <EditableSpan
            id="basic.phone"
            focusedField={focusedField}
            setFocusedField={setFocusedField}
            value={data.basic.phone}
            onBlur={(v) => setBasic("phone", v)}
            className="outline-none min-w-[1ch]"
          />
          <span style={{ margin: "0 10px" }} />
          <EditableSpan
            id="basic.email"
            focusedField={focusedField}
            setFocusedField={setFocusedField}
            value={data.basic.email}
            onBlur={(v) => setBasic("email", v)}
            className="outline-none min-w-[1ch]"
          />
          <span style={{ margin: "0 10px" }} />
          <EditableSpan
            id="basic.location"
            focusedField={focusedField}
            setFocusedField={setFocusedField}
            value={data.basic.location}
            onBlur={(v) => setBasic("location", v)}
            className="outline-none min-w-[1ch]"
          />
        </p>
      </header>

      {/* ===== 자기소개 ===== */}
      <section style={{ marginBottom: "18px" }}>
        <h2
          className="section-title"
          style={{
            fontSize: "10.5pt",
            fontWeight: 700,
            color: "#111",
            letterSpacing: "-0.02em",
            marginBottom: "8px",
            paddingBottom: "4px",
            borderBottom: "1px solid #ddd",
          }}
        >
          자기소개
        </h2>
        <EditableBlock
          id="intro"
          focusedField={focusedField}
          setFocusedField={setFocusedField}
          value={data.intro}
          onBlur={setIntro}
          style={{
            fontSize: "10pt",
            color: "#333",
            lineHeight: 1.65,
            textAlign: "justify",
          }}
          className="outline-none"
        />
      </section>

      {/* ===== 학력 ===== */}
      <section style={{ marginBottom: "18px" }}>
        <h2
          style={{
            fontSize: "10.5pt",
            fontWeight: 700,
            color: "#111",
            letterSpacing: "-0.02em",
            marginBottom: "8px",
            paddingBottom: "4px",
            borderBottom: "1px solid #ddd",
          }}
        >
          학력
        </h2>
        {data.education.map((e, i) => (
          <div key={i} style={{ marginBottom: "12px" }}>
            <div
              style={{
                fontWeight: 600,
                color: "#111",
                fontSize: "10.5pt",
                marginBottom: "2px",
              }}
            >
              <EditableSpan
                id={`edu.${i}.school`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={e.school}
                onBlur={(v) => setEducation(i, { school: v })}
                className="outline-none min-w-[1ch]"
              />
            </div>
            <div style={{ fontSize: "9.5pt", color: "#666", marginBottom: "5px" }}>
              <EditableSpan
                id={`edu.${i}.info`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={e.info}
                onBlur={(v) => setEducation(i, { info: v })}
                className="outline-none min-w-[1ch]"
              />
            </div>
            <div style={{ fontSize: "9.5pt", color: "#666", marginBottom: "5px" }}>
              <EditableSpan
                id={`edu.${i}.period`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={e.period}
                onBlur={(v) => setEducation(i, { period: v })}
                className="outline-none min-w-[1ch]"
              />
            </div>
            {e.desc && (
              <div
                style={{
                  listStyle: "none",
                  paddingLeft: 0,
                  fontSize: "10pt",
                  color: "#333",
                }}
              >
                <EditableBlock
                  id={`edu.${i}.desc`}
                  focusedField={focusedField}
                  setFocusedField={setFocusedField}
                  value={e.desc}
                  onBlur={(v) => setEducation(i, { desc: v || undefined })}
                  className="outline-none"
                />
              </div>
            )}
          </div>
        ))}
      </section>

      {/* ===== 경력사항 ===== */}
      <section style={{ marginBottom: "18px" }}>
        <h2
          style={{
            fontSize: "10.5pt",
            fontWeight: 700,
            color: "#111",
            letterSpacing: "-0.02em",
            marginBottom: "8px",
            paddingBottom: "4px",
            borderBottom: "1px solid #ddd",
          }}
        >
          경력사항
        </h2>
        {data.experience.map((exp, i) => (
          <div key={i} style={{ marginBottom: "12px" }}>
            <div
              style={{
                fontWeight: 600,
                color: "#111",
                fontSize: "10.5pt",
                marginBottom: "2px",
              }}
            >
              <EditableSpan
                id={`exp.${i}.company`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={exp.company}
                onBlur={(v) => setExperience(i, { company: v })}
                className="outline-none min-w-[1ch]"
              />
              {" · "}
              <EditableSpan
                id={`exp.${i}.role`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={exp.role}
                onBlur={(v) => setExperience(i, { role: v })}
                className="outline-none min-w-[1ch]"
              />
            </div>
            <div style={{ fontSize: "9.5pt", color: "#666", marginBottom: "5px" }}>
              <EditableSpan
                id={`exp.${i}.period`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={exp.period}
                onBlur={(v) => setExperience(i, { period: v })}
                className="outline-none min-w-[1ch]"
              />
            </div>
            <ul style={{ listStyle: "none", paddingLeft: 0, margin: 0 }}>
              {exp.bullets.map((b, j) => (
                <EditableLi
                  key={j}
                  id={`exp.${i}.bullet.${j}`}
                  focusedField={focusedField}
                  setFocusedField={setFocusedField}
                  value={b}
                  onBlur={(v) => setExperienceBullet(i, j, v)}
                />
              ))}
            </ul>
          </div>
        ))}
      </section>

      {/* ===== 프로젝트 / 대외활동 ===== */}
      <section style={{ marginBottom: "18px" }}>
        <h2
          style={{
            fontSize: "10.5pt",
            fontWeight: 700,
            color: "#111",
            letterSpacing: "-0.02em",
            marginBottom: "8px",
            paddingBottom: "4px",
            borderBottom: "1px solid #ddd",
          }}
        >
          프로젝트 / 대외활동
        </h2>
        {data.nonDevelopExperience.map((item, i) => (
          <div key={`nde-${i}`} style={{ marginBottom: "12px" }}>
            <div
              style={{
                fontWeight: 600,
                color: "#111",
                fontSize: "10.5pt",
                marginBottom: "2px",
              }}
            >
              <EditableSpan
                id={`nde.${i}.role`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={item.role}
                onBlur={(v) =>
                  setData((prev) => {
                    const next = [...prev.nonDevelopExperience];
                    next[i] = { ...next[i], role: v };
                    return { ...prev, nonDevelopExperience: next };
                  })
                }
                className="outline-none min-w-[1ch]"
              />
            </div>
            <div style={{ fontSize: "9.5pt", color: "#666" }}>
              <EditableSpan
                id={`nde.${i}.period`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={item.period}
                onBlur={(v) =>
                  setData((prev) => {
                    const next = [...prev.nonDevelopExperience];
                    next[i] = { ...next[i], period: v };
                    return { ...prev, nonDevelopExperience: next };
                  })
                }
                className="outline-none min-w-[1ch]"
              />
            </div>
          </div>
        ))}
        {data.projects.map((p, i) => (
          <div key={i} style={{ marginBottom: "12px" }}>
            <div
              style={{
                fontWeight: 600,
                color: "#111",
                fontSize: "10.5pt",
                marginBottom: "2px",
              }}
            >
              <EditableSpan
                id={`proj.${i}.title`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={p.title}
                onBlur={(v) => setProject(i, { title: v })}
                className="outline-none min-w-[1ch]"
              />
            </div>
            <div style={{ fontSize: "9.5pt", color: "#666", marginBottom: "5px" }}>
              <EditableSpan
                id={`proj.${i}.type`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={p.type}
                onBlur={(v) => setProject(i, { type: v })}
                className="outline-none min-w-[1ch]"
              />
            </div>
            <div
              style={{
                fontSize: "10pt",
                color: "#333",
                marginBottom: "4px",
              }}
            >
              <EditableBlock
                id={`proj.${i}.desc`}
                focusedField={focusedField}
                setFocusedField={setFocusedField}
                value={p.desc}
                onBlur={(v) => setProject(i, { desc: v })}
                className="outline-none"
              />
            </div>
          </div>
        ))}
      </section>

      {/* ===== 수상 · 자격증 · 어학 ===== */}
      <section style={{ marginBottom: "18px" }}>
        <h2
          style={{
            fontSize: "10.5pt",
            fontWeight: 700,
            color: "#111",
            letterSpacing: "-0.02em",
            marginBottom: "8px",
            paddingBottom: "4px",
            borderBottom: "1px solid #ddd",
          }}
        >
          수상 · 자격증 · 어학
        </h2>
        <ul
          style={{
            listStyle: "none",
            paddingLeft: 0,
            margin: 0,
          }}
        >
          {data.awards.map((a, i) => (
            <EditableLi
              key={i}
              id={`award.${i}`}
              focusedField={focusedField}
              setFocusedField={setFocusedField}
              value={a}
              onBlur={(v) => setAwards(i, v)}
            />
          ))}
        </ul>
      </section>

      {/* ===== 핵심 역량 · 기술 ===== */}
      <section style={{ marginBottom: "18px" }}>
        <h2
          style={{
            fontSize: "10.5pt",
            fontWeight: 700,
            color: "#111",
            letterSpacing: "-0.02em",
            marginBottom: "8px",
            paddingBottom: "4px",
            borderBottom: "1px solid #ddd",
          }}
        >
          핵심 역량 · 기술
        </h2>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "6px 12px",
          }}
        >
          {data.skillGroups.map((g, gi) =>
            g.tags.map((tag, ti) => (
              <span
                key={`${gi}-${ti}`}
                style={{
                  fontSize: "9.5pt",
                  padding: "4px 12px",
                  background: "#f5f5f5",
                  color: "#333",
                  borderRadius: "4px",
                  fontWeight: 500,
                }}
              >
                <EditableSpan
                  id={`skill.${gi}.${ti}`}
                  focusedField={focusedField}
                  setFocusedField={setFocusedField}
                  value={tag}
                  onBlur={(v) => setSkillTag(gi, ti, v)}
                  className="outline-none min-w-[1ch]"
                />
              </span>
            ))
          )}
        </div>
      </section>

      {/* Noto Sans KR 폰트 로드 (HTML 양식과 동일) */}
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap"
      />
    </div>
  );
}
