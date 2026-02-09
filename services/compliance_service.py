"""
Compliance And Reporting Service
Service methods for legal compliance, auditing, and reporting
"""

from datetime import datetime, timedelta
from models.compliance import (
    ComplianceObligation, DeadlineTracker, AuditLog, CustodyAffidavit,
    CertificationOfCustody, ComplianceReport, RiskAssessment,
    LegalHold_Evidence, DocumentRetention
)
from models.evidence import EvidenceItem
from models.legal_case import LegalCase
from auth.models import db, User
import json
from uuid import uuid4


class ComplianceService:
    """Service for managing compliance obligations"""
    
    @staticmethod
    def create_compliance_obligation(case_id, obligation_data, created_by_user):
        """Create a compliance obligation"""
        obligation = ComplianceObligation(
            case_id=case_id,
            obligation_name=obligation_data['obligation_name'],
            obligation_type=obligation_data['obligation_type'],
            regulation=obligation_data.get('regulation'),
            description=obligation_data.get('description'),
            identified_date=datetime.utcnow(),
            deadline=obligation_data['deadline'],
            required_actions=json.dumps(obligation_data.get('required_actions', [])),
            responsible_party=obligation_data.get('responsible_party'),
            assigned_to_id=obligation_data.get('assigned_to_id'),
            risk_level=obligation_data.get('risk_level', 'medium')
        )
        
        db.session.add(obligation)
        db.session.commit()
        
        # Log this action
        AuditLogService.log_action(
            case_id=case_id,
            activity_type='compliance_obligation_created',
            entity_type='ComplianceObligation',
            entity_id=str(obligation.id),
            user_id=created_by_user.id,
            description=f'Created obligation: {obligation.obligation_name}'
        )
        
        return obligation
    
    @staticmethod
    def update_obligation_status(obligation_id, new_status, updated_by_user):
        """Update compliance obligation status"""
        obligation = ComplianceObligation.query.get(obligation_id)
        if not obligation:
            return None
        
        old_status = obligation.status
        obligation.status = new_status
        
        if new_status == 'completed':
            obligation.completed_date = datetime.utcnow()
            obligation.is_met = True
        
        db.session.commit()
        
        return obligation
    
    @staticmethod
    def certify_obligation(obligation_id, certified_by_user):
        """Certify that an obligation has been met"""
        obligation = ComplianceObligation.query.get(obligation_id)
        if not obligation:
            return None
        
        obligation.certification_status = 'certified'
        obligation.certified_by_id = certified_by_user.id
        obligation.certified_date = datetime.utcnow()
        db.session.commit()
        
        return obligation
    
    @staticmethod
    def get_case_obligations(case_id, status_filter=None):
        """Get all obligations for a case"""
        query = ComplianceObligation.query.filter_by(case_id=case_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        return query.order_by(ComplianceObligation.deadline).all()
    
    @staticmethod
    def get_overdue_obligations(case_id):
        """Get overdue compliance obligations"""
        return ComplianceObligation.query.filter(
            ComplianceObligation.case_id == case_id,
            ComplianceObligation.deadline < datetime.utcnow(),
            ComplianceObligation.status.in_(['pending', 'in_progress'])
        ).all()
    
    @staticmethod
    def get_compliance_dashboard(case_id):
        """Get comprehensive compliance dashboard data"""
        obligations = ComplianceObligation.query.filter_by(case_id=case_id).all()
        
        dashboard = {
            'total_obligations': len(obligations),
            'completed': sum(1 for o in obligations if o.status == 'completed'),
            'pending': sum(1 for o in obligations if o.status == 'pending'),
            'in_progress': sum(1 for o in obligations if o.status == 'in_progress'),
            'overdue': sum(1 for o in obligations if o.deadline < datetime.utcnow() and o.status != 'completed'),
            'compliance_percentage': 0,
            'by_type': {},
            'upcomming_deadlines': []
        }
        
        # Calculate compliance percentage
        if obligations:
            dashboard['compliance_percentage'] = (dashboard['completed'] / len(obligations)) * 100
        
        # Group by type
        for obligation in obligations:
            ob_type = obligation.obligation_type
            if ob_type not in dashboard['by_type']:
                dashboard['by_type'][ob_type] = {'total': 0, 'completed': 0}
            dashboard['by_type'][ob_type]['total'] += 1
            if obligation.status == 'completed':
                dashboard['by_type'][ob_type]['completed'] += 1
        
        # Get upcoming deadlines (next 7 days)
        upcoming = ComplianceObligation.query.filter(
            ComplianceObligation.case_id == case_id,
            ComplianceObligation.deadline >= datetime.utcnow(),
            ComplianceObligation.deadline <= datetime.utcnow() + timedelta(days=7),
            ComplianceObligation.status != 'completed'
        ).order_by(ComplianceObligation.deadline).all()
        
        dashboard['upcomming_deadlines'] = [
            {'name': o.obligation_name, 'deadline': o.deadline.isoformat()}
            for o in upcoming
        ]
        
        return dashboard


class DeadlineService:
    """Service for managing case deadlines"""
    
    @staticmethod
    def create_deadline(case_id, deadline_data, created_by_user):
        """Create a case deadline"""
        deadline = DeadlineTracker(
            case_id=case_id,
            deadline_name=deadline_data['deadline_name'],
            deadline_date=deadline_data['deadline_date'],
            deadline_type=deadline_data.get('deadline_type'),
            court_order=deadline_data.get('court_order'),
            regulation=deadline_data.get('regulation'),
            responsible_party=deadline_data.get('responsible_party'),
            assigned_to_id=deadline_data.get('assigned_to_id'),
            notes=deadline_data.get('notes')
        )
        
        db.session.add(deadline)
        db.session.commit()
        
        return deadline
    
    @staticmethod
    def check_deadline_alerts(case_id):
        """Check for approaching deadlines"""
        upcoming = DeadlineTracker.query.filter(
            DeadlineTracker.case_id == case_id,
            DeadlineTracker.status == 'pending',
            DeadlineTracker.deadline_date <= datetime.utcnow() + timedelta(days=7),
            DeadlineTracker.deadline_date > datetime.utcnow(),
            DeadlineTracker.alert_sent == False
        ).all()
        
        return upcoming
    
    @staticmethod
    def mark_alert_sent(deadline_id):
        """Mark deadline alert as sent"""
        deadline = DeadlineTracker.query.get(deadline_id)
        if deadline:
            deadline.alert_sent = True
            deadline.alert_sent_date = datetime.utcnow()
            db.session.commit()


class AuditLogService:
    """Service for audit logging"""
    
    @staticmethod
    def log_action(case_id=None, evidence_id=None, activity_type=None, entity_type=None,
                   entity_id=None, user_id=None, username=None, old_value=None, new_value=None,
                   description=None, ip_address='', user_agent='', success=True, error_message=None):
        """Log an action in the audit log"""
        log_entry = AuditLog(
            case_id=case_id,
            evidence_id=evidence_id,
            activity_type=activity_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            username=username,
            old_value=old_value,
            new_value=new_value,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return log_entry
    
    @staticmethod
    def get_case_audit_log(case_id, limit=100):
        """Get audit log entries for a case"""
        return AuditLog.query.filter_by(case_id=case_id).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_evidence_audit_log(evidence_id, limit=100):
        """Get audit log entries for evidence"""
        return AuditLog.query.filter_by(evidence_id=evidence_id).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_user_audit_log(user_id, days=30):
        """Get audit log for a user's activities"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= cutoff_date
        ).order_by(AuditLog.timestamp.desc()).all()


class CustodyService:
    """Service for managing chain of custody documentation"""
    
    @staticmethod
    def create_custody_affidavit(case_id, affidavit_data, evidence_id=None):
        """Create a custody affidavit"""
        affidavit = CustodyAffidavit(
            case_id=case_id,
            evidence_id=evidence_id,
            affiant_name=affidavit_data['affiant_name'],
            affiant_title=affidavit_data.get('affiant_title'),
            affiant_organization=affidavit_data.get('affiant_organization'),
            affiant_contact=affidavit_data.get('affiant_contact'),
            affidavit_date=affidavit_data.get('affidavit_date', datetime.utcnow()),
            custody_statement=affidavit_data['custody_statement'],
            materials_described=affidavit_data['materials_described'],
            sworn_under_penalty=affidavit_data.get('sworn_under_penalty', True),
            jurisdiction=affidavit_data.get('jurisdiction')
        )
        
        db.session.add(affidavit)
        db.session.commit()
        
        return affidavit
    
    @staticmethod
    def create_certification_of_custody(case_id, cert_data, certified_by_user):
        """Create certification of custody"""
        cert_number = f"COC-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        certification = CertificationOfCustody(
            case_id=case_id,
            certification_date=datetime.utcnow(),
            certification_number=cert_number,
            certifying_officer=cert_data['certifying_officer'],
            title=cert_data.get('title'),
            organization=cert_data.get('organization'),
            materials_description=cert_data['materials_description'],
            total_items=cert_data.get('total_items'),
            certification_statement=cert_data['certification_statement'],
            maintained_integrity=cert_data.get('maintained_integrity', True),
            not_altered=cert_data.get('not_altered', True),
            proper_storage=cert_data.get('proper_storage', True),
            access_controlled=cert_data.get('access_controlled', True),
            submitted_by_id=certified_by_user.id
        )
        
        db.session.add(certification)
        db.session.commit()
        
        return certification


class ComplianceReportingService:
    """Service for generating compliance reports"""
    
    @staticmethod
    def generate_compliance_report(case_id, report_type, report_data, generated_by_user):
        """Generate a compliance report"""
        report = ComplianceReport(
            case_id=case_id,
            report_name=report_data['report_name'],
            report_type=report_type,
            report_period_start=report_data.get('report_period_start'),
            report_period_end=report_data.get('report_period_end'),
            report_summary=report_data.get('report_summary'),
            detailed_findings=json.dumps(report_data.get('detailed_findings', {})),
            recommendations=json.dumps(report_data.get('recommendations', [])),
            overall_compliance_status=report_data.get('compliance_status', 'needs_review'),
            compliance_percentage=report_data.get('compliance_percentage', 0),
            critical_issues=report_data.get('critical_issues', 0),
            major_issues=report_data.get('major_issues', 0),
            minor_issues=report_data.get('minor_issues', 0),
            reviewed_by_id=generated_by_user.id
        )
        
        db.session.add(report)
        db.session.commit()
        
        return report
    
    @staticmethod
    def approve_report(report_id, approved_by_user):
        """Approve a compliance report"""
        report = ComplianceReport.query.get(report_id)
        if not report:
            return None
        
        report.approved = True
        report.approved_by_id = approved_by_user.id
        report.approved_date = datetime.utcnow()
        db.session.commit()
        
        return report
    
    @staticmethod
    def get_case_reports(case_id, report_type=None):
        """Get compliance reports for a case"""
        query = ComplianceReport.query.filter_by(case_id=case_id)
        
        if report_type:
            query = query.filter_by(report_type=report_type)
        
        return query.order_by(ComplianceReport.generated_at.desc()).all()


class RiskAssessmentService:
    """Service for risk assessments"""
    
    @staticmethod
    def create_risk_assessment(case_id, assessment_data, assessed_by_user):
        """Create a risk assessment"""
        # Calculate risk score
        probability = assessment_data.get('probability', 0.5)
        impact = assessment_data.get('impact', 0.5)
        risk_score = probability * impact
        
        assessment = RiskAssessment(
            case_id=case_id,
            assessment_name=assessment_data['assessment_name'],
            assessment_date=datetime.utcnow(),
            risk_area=assessment_data['risk_area'],
            risk_level=assessment_data['risk_level'],
            probability=probability,
            impact=impact,
            risk_score=risk_score,
            risk_description=assessment_data['risk_description'],
            potential_consequences=assessment_data.get('potential_consequences'),
            mitigation_strategy=assessment_data.get('mitigation_strategy'),
            responsible_party=assessment_data.get('responsible_party'),
            mitigation_deadline=assessment_data.get('mitigation_deadline'),
            monitoring_plan=assessment_data.get('monitoring_plan'),
            assessed_by_id=assessed_by_user.id
        )
        
        db.session.add(assessment)
        db.session.commit()
        
        return assessment
    
    @staticmethod
    def update_risk_status(assessment_id, new_status):
        """Update risk mitigation status"""
        assessment = RiskAssessment.query.get(assessment_id)
        if assessment:
            assessment.status = new_status
            db.session.commit()
        
        return assessment
    
    @staticmethod
    def get_open_risks(case_id):
        """Get open risks for a case"""
        return RiskAssessment.query.filter(
            RiskAssessment.case_id == case_id,
            RiskAssessment.status.in_(['pending', 'in_progress'])
        ).order_by(RiskAssessment.risk_score.desc()).all()


class RetentionService:
    """Service for document retention and destruction"""
    
    @staticmethod
    def create_retention_plan(evidence_id, case_id, retention_data):
        """Create document retention plan"""
        retention = DocumentRetention(
            evidence_id=evidence_id,
            case_id=case_id,
            retention_policy=retention_data['retention_policy'],
            retention_period=retention_data.get('retention_period'),
            scheduled_destruction_date=retention_data.get('scheduled_destruction_date'),
            is_under_legal_hold=retention_data.get('is_under_legal_hold', False),
            hold_reason=retention_data.get('hold_reason')
        )
        
        db.session.add(retention)
        db.session.commit()
        
        return retention
    
    @staticmethod
    def approve_destruction(retention_id, approved_by_user):
        """Approve document destruction"""
        retention = DocumentRetention.query.get(retention_id)
        if retention:
            retention.destruction_approved = True
            retention.destruction_approved_by_id = approved_by_user.id
            retention.destruction_approved_date = datetime.utcnow()
            db.session.commit()
        
        return retention
    
    @staticmethod
    def complete_destruction(retention_id, destruction_method, completed_by_user):
        """Record document destruction completion"""
        retention = DocumentRetention.query.get(retention_id)
        if retention:
            retention.destruction_completed = True
            retention.destruction_date = datetime.utcnow()
            retention.destruction_method = destruction_method
            retention.destruction_completed_by_id = completed_by_user.id
            db.session.commit()
        
        return retention
    
    @staticmethod
    def get_candidates_for_destruction(case_id, days_before_date=None):
        """Get documents eligible for destruction"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_before_date or 30)
        
        return DocumentRetention.query.filter(
            DocumentRetention.case_id == case_id,
            DocumentRetention.scheduled_destruction_date <= cutoff_date,
            DocumentRetention.destruction_approved == True,
            DocumentRetention.destruction_completed == False,
            DocumentRetention.is_under_legal_hold == False
        ).all()


class HoldEvidenceLinkService:
    """Service for linking evidence to litigation holds"""
    
    @staticmethod
    def link_evidence_to_hold(hold_id, evidence_ids, preservation_method='backup'):
        """Link evidence items to a litigation hold"""
        links = []
        for evidence_id in evidence_ids:
            # Check if already linked
            existing = LegalHold_Evidence.query.filter_by(
                hold_id=hold_id,
                evidence_id=evidence_id
            ).first()
            
            if not existing:
                link = LegalHold_Evidence(
                    hold_id=hold_id,
                    evidence_id=evidence_id,
                    preservation_method=preservation_method
                )
                db.session.add(link)
                links.append(link)
        
        db.session.commit()
        
        return links
    
    @staticmethod
    def release_evidence_from_hold(hold_id, evidence_id, release_reason):
        """Release evidence from a litigation hold"""
        link = LegalHold_Evidence.query.filter_by(
            hold_id=hold_id,
            evidence_id=evidence_id
        ).first()
        
        if link:
            link.status = 'released'
            link.released_date = datetime.utcnow()
            link.release_reason = release_reason
            db.session.commit()
        
        return link
    
    @staticmethod
    def get_evidence_count_in_hold(hold_id):
        """Get count of evidence items in a hold"""
        return LegalHold_Evidence.query.filter_by(hold_id=hold_id, status='held').count()
