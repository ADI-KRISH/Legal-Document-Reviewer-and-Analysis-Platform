import "./Header.css";

export function Header({ title, subtitle }) {
    return (
        <header className="header">
            <div>
                <h1 className="header-title">{title}</h1>
                {subtitle && <p className="header-sub">{subtitle}</p>}
            </div>
            <div className="header-right">
                <div className="header-pill">
                    <span className="status-dot status-dot--green" style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--success)', boxShadow: '0 0 6px var(--success)', display: 'inline-block' }} />
                    <span>AI Ready</span>
                </div>
            </div>
        </header>
    );
}
