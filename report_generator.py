"""
Report Generator - Creates HTML diagnostic reports with charts and styling.
"""

import json
import os
from datetime import datetime


class ReportGenerator:
    """Generates a beautiful HTML report from scan results and AI analysis."""

    def generate(self, scan_results: dict, issues: list, health_score: float, ai_analysis: dict) -> str:
        """Generate and save an HTML report, returning the file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"PC_Diagnostic_Report_{timestamp}.html"
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

        html = self._build_html(scan_results, issues, health_score, ai_analysis)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return filepath

    def _build_html(self, scan_results, issues, health_score, ai_analysis):
        rating = ai_analysis.get("health_rating", "Unknown")
        rating_color = {
            "Excellent": "#22c55e", "Good": "#84cc16", "Fair": "#eab308",
            "Poor": "#f97316", "Critical": "#ef4444"
        }.get(rating, "#6b7280")

        critical_count = len([i for i in issues if i.severity == "critical"])
        warning_count = len([i for i in issues if i.severity == "warning"])
        info_count = len([i for i in issues if i.severity == "info"])

        issues_html = ""
        for issue in issues:
            sev_color = {"critical": "#ef4444", "warning": "#f59e0b", "info": "#3b82f6"}.get(issue.severity, "#6b7280")
            issues_html += f"""
            <div class="issue-card" style="border-left: 4px solid {sev_color};">
                <div class="issue-header">
                    <span class="severity-badge" style="background:{sev_color};">{issue.severity.upper()}</span>
                    <span class="issue-title">{issue.title}</span>
                    <span class="issue-category">{issue.category}</span>
                </div>
                <p class="issue-desc">{issue.description}</p>
                <p class="issue-fix"><strong>Fix:</strong> {issue.recommendation}</p>
            </div>"""

        tips_html = ""
        for tip in ai_analysis.get("optimization_tips", []):
            tips_html += f"""
            <div class="tip-card">
                <div class="tip-area">{tip.get('area', '')}</div>
                <p>{tip.get('tip', '')}</p>
                <span class="tip-improvement">{tip.get('expected_improvement', '')}</span>
            </div>"""

        system_data = scan_results.get("system", None)
        sys_info = ""
        if system_data:
            d = system_data.data
            sys_info = f"""
            <table class="info-table">
                <tr><td>OS</td><td>{d.get('os_name', d.get('os_edition', 'N/A'))}</td></tr>
                <tr><td>Hostname</td><td>{d.get('hostname', 'N/A')}</td></tr>
                <tr><td>Architecture</td><td>{d.get('architecture', 'N/A')}</td></tr>
                <tr><td>Uptime</td><td>{d.get('uptime_human', 'N/A')}</td></tr>
                <tr><td>Boot Time</td><td>{d.get('boot_time', 'N/A')}</td></tr>
                <tr><td>Motherboard</td><td>{d.get('motherboard_manufacturer', '')} {d.get('motherboard', 'N/A')}</td></tr>
                <tr><td>BIOS</td><td>{d.get('bios_manufacturer', '')} {d.get('bios_version', 'N/A')}</td></tr>
            </table>"""

        cpu_data = scan_results.get("cpu", None)
        cpu_info = ""
        if cpu_data:
            d = cpu_data.data
            cpu_info = f"""
            <table class="info-table">
                <tr><td>Processor</td><td>{d.get('processor', 'N/A')}</td></tr>
                <tr><td>Cores</td><td>{d.get('physical_cores', '?')} Physical / {d.get('logical_cores', '?')} Logical</td></tr>
                <tr><td>Frequency</td><td>{d.get('current_frequency_mhz', 'N/A')} MHz (Max: {d.get('max_frequency_mhz', 'N/A')} MHz)</td></tr>
                <tr><td>Average Usage</td><td>{d.get('average_usage_percent', 'N/A')}%</td></tr>
                <tr><td>Temperature</td><td>{d.get('temperature_celsius', 'N/A')}°C</td></tr>
            </table>"""

        mem_data = scan_results.get("memory", None)
        mem_info = ""
        if mem_data:
            d = mem_data.data
            mem_info = f"""
            <table class="info-table">
                <tr><td>Total RAM</td><td>{d.get('total_gb', 'N/A')} GB</td></tr>
                <tr><td>Used</td><td>{d.get('used_gb', 'N/A')} GB ({d.get('usage_percent', 'N/A')}%)</td></tr>
                <tr><td>Available</td><td>{d.get('available_gb', 'N/A')} GB</td></tr>
                <tr><td>Swap Total</td><td>{d.get('swap_total_gb', 'N/A')} GB</td></tr>
                <tr><td>Swap Used</td><td>{d.get('swap_used_gb', 'N/A')} GB ({d.get('swap_usage_percent', 'N/A')}%)</td></tr>
            </table>
            <div class="bar-container">
                <div class="bar-fill" style="width:{d.get('usage_percent', 0)}%; background:{'#ef4444' if d.get('usage_percent', 0) > 85 else '#22c55e' if d.get('usage_percent', 0) < 60 else '#eab308'};">
                    {d.get('usage_percent', 0)}%
                </div>
            </div>"""

        disk_data = scan_results.get("disk", None)
        disk_info = ""
        if disk_data:
            for part in disk_data.data.get("partitions", []):
                pct = part.get('usage_percent', 0)
                color = '#ef4444' if pct > 90 else '#eab308' if pct > 75 else '#22c55e'
                disk_info += f"""
                <div class="disk-part">
                    <strong>{part.get('device', '?')} ({part.get('mountpoint', '?')})</strong>
                    <span>{part.get('filesystem', '?')} | {part.get('used_gb', '?')}GB / {part.get('total_gb', '?')}GB</span>
                    <div class="bar-container">
                        <div class="bar-fill" style="width:{pct}%; background:{color};">{pct}%</div>
                    </div>
                </div>"""

        net_data = scan_results.get("network", None)
        net_info = ""
        if net_data:
            d = net_data.data
            net_info = f"""
            <table class="info-table">
                <tr><td>Internet</td><td>{'Connected' if d.get('internet_connected') else 'Disconnected'}</td></tr>
                <tr><td>DNS</td><td>{'Working' if d.get('dns_working') else 'Not Working'}</td></tr>
                <tr><td>Latency</td><td>{d.get('latency_ms', 'N/A')} ms</td></tr>
                <tr><td>Data Sent</td><td>{d.get('bytes_sent_gb', 'N/A')} GB</td></tr>
                <tr><td>Data Received</td><td>{d.get('bytes_recv_gb', 'N/A')} GB</td></tr>
                <tr><td>Errors (In/Out)</td><td>{d.get('errors_in', 0)} / {d.get('errors_out', 0)}</td></tr>
            </table>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PC Doctor AI Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }}
        .container {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}
        .header {{ text-align: center; padding: 2rem 0; border-bottom: 2px solid #1e293b; margin-bottom: 2rem; }}
        .header h1 {{ font-size: 2.2rem; background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .header .subtitle {{ color: #94a3b8; margin-top: 0.5rem; }}
        .health-score {{ display: flex; align-items: center; justify-content: center; gap: 2rem; margin: 2rem 0; padding: 2rem; background: #1e293b; border-radius: 16px; }}
        .score-circle {{ width: 140px; height: 140px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: bold; border: 6px solid {rating_color}; color: {rating_color}; }}
        .score-details {{ text-align: left; }}
        .score-details h2 {{ color: {rating_color}; font-size: 1.5rem; }}
        .score-details .counts {{ display: flex; gap: 1rem; margin-top: 0.5rem; }}
        .count-badge {{ padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; }}
        .section {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }}
        .section h2 {{ color: #60a5fa; font-size: 1.3rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #334155; }}
        .issue-card {{ background: #0f172a; padding: 1rem; border-radius: 8px; margin-bottom: 0.8rem; }}
        .issue-header {{ display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.5rem; }}
        .severity-badge {{ padding: 2px 10px; border-radius: 12px; color: white; font-size: 0.75rem; font-weight: 600; }}
        .issue-title {{ font-weight: 600; color: #f1f5f9; }}
        .issue-category {{ color: #64748b; font-size: 0.85rem; margin-left: auto; }}
        .issue-desc {{ color: #94a3b8; font-size: 0.9rem; }}
        .issue-fix {{ color: #86efac; font-size: 0.9rem; margin-top: 0.5rem; }}
        .tip-card {{ background: #0f172a; padding: 1rem; border-radius: 8px; margin-bottom: 0.8rem; border-left: 3px solid #8b5cf6; }}
        .tip-area {{ color: #a78bfa; font-weight: 600; margin-bottom: 0.3rem; }}
        .tip-improvement {{ color: #34d399; font-size: 0.85rem; }}
        .info-table {{ width: 100%; border-collapse: collapse; }}
        .info-table td {{ padding: 8px 12px; border-bottom: 1px solid #334155; }}
        .info-table td:first-child {{ color: #94a3b8; width: 200px; font-weight: 500; }}
        .bar-container {{ background: #334155; border-radius: 8px; height: 24px; margin: 0.5rem 0; overflow: hidden; }}
        .bar-fill {{ height: 100%; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 600; color: white; min-width: 40px; transition: width 0.5s; }}
        .disk-part {{ margin-bottom: 1rem; }}
        .disk-part span {{ color: #94a3b8; font-size: 0.85rem; }}
        .ai-assessment {{ background: linear-gradient(135deg, #1e1b4b, #1e293b); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid #3730a3; }}
        .ai-assessment h2 {{ color: #a78bfa; }}
        .ai-assessment p {{ color: #c4b5fd; line-height: 1.8; }}
        .footer {{ text-align: center; color: #475569; padding: 2rem 0; font-size: 0.85rem; border-top: 1px solid #1e293b; margin-top: 2rem; }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
        @media (max-width: 768px) {{ .grid-2 {{ grid-template-columns: 1fr; }} .health-score {{ flex-direction: column; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PC Doctor AI Report</h1>
            <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')} | Analysis: {ai_analysis.get('analysis_type', 'Unknown')}</p>
        </div>

        <div class="health-score">
            <div class="score-circle">{health_score:.0f}</div>
            <div class="score-details">
                <h2>{rating}</h2>
                <p>Overall System Health Score</p>
                <div class="counts">
                    <span class="count-badge" style="background:#ef4444;">{critical_count} Critical</span>
                    <span class="count-badge" style="background:#f59e0b;color:#000;">{warning_count} Warnings</span>
                    <span class="count-badge" style="background:#3b82f6;">{info_count} Info</span>
                </div>
            </div>
        </div>

        <div class="ai-assessment">
            <h2>AI Assessment</h2>
            <p>{ai_analysis.get('overall_assessment', 'No assessment available.')}</p>
        </div>

        {'<div class="section"><h2>Issues Found</h2>' + issues_html + '</div>' if issues_html else '<div class="section"><h2>No Issues Found</h2><p style="color:#22c55e;">Your system appears to be healthy!</p></div>'}

        <div class="section">
            <h2>Optimization Tips</h2>
            {tips_html}
        </div>

        <div class="grid-2">
            <div class="section">
                <h2>System Information</h2>
                {sys_info}
            </div>
            <div class="section">
                <h2>CPU</h2>
                {cpu_info}
            </div>
        </div>

        <div class="grid-2">
            <div class="section">
                <h2>Memory</h2>
                {mem_info}
            </div>
            <div class="section">
                <h2>Network</h2>
                {net_info}
            </div>
        </div>

        <div class="section">
            <h2>Storage</h2>
            {disk_info}
        </div>

        <div class="section">
            <h2>Hardware Recommendations</h2>
            <p>{ai_analysis.get('hardware_recommendations', 'No recommendations at this time.')}</p>
        </div>

        <div class="section">
            <h2>Maintenance Schedule</h2>
            <p>{ai_analysis.get('maintenance_schedule', 'Follow standard maintenance practices.')}</p>
        </div>

        <div class="footer">
            <p>PC Doctor AI - Smart System Analyzer</p>
            <p>This report is for informational purposes. Always back up data before making system changes.</p>
        </div>
    </div>
</body>
</html>"""
