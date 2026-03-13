package com.grievance.repository;

import com.grievance.model.Complaint;
import com.grievance.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ComplaintRepository extends JpaRepository<Complaint, Long> {
    List<Complaint> findByUser(User user);
    List<Complaint> findByStatus(String status);
}
