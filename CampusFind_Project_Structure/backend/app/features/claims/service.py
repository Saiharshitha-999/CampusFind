from app.core.time import utc_isoformat


def claim_data(claim, include_proof=True):
    return {'id':claim.id,'claim_id':claim.id,'report_id':claim.report_id,'item_id':claim.report_id,
            **({'claimant_id':claim.claimant_id,'proof_reference':claim.proof_reference,
                'has_proof_file':bool(claim.proof_reference)} if include_proof else {}),
            'status':claim.status,'reviewer_id':claim.reviewer_id,
            'decision_comment':claim.decision_comment,'created_at':utc_isoformat(claim.created_at),
            'decided_at':utc_isoformat(claim.decided_at) if claim.decided_at else None}
