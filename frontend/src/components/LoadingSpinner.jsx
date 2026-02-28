export function LoadingSpinner({ size = 28, text }) {
    return (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.75rem" }}>
            <div
                style={{
                    width: size,
                    height: size,
                    border: "3px solid rgba(99,102,241,0.2)",
                    borderTop: "3px solid var(--accent)",
                    borderRadius: "50%",
                    animation: "spin 0.75s linear infinite",
                }}
            />
            {text && <span style={{ color: "var(--text-2)", fontSize: "0.85rem" }}>{text}</span>}
        </div>
    );
}
