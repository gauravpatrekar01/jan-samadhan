package com.grievance.repository;

import com.grievance.model.ComplaintStatusHistory;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ComplaintStatusHistoryRepository extends JpaRepository<ComplaintStatusHistory, Long> {
}
