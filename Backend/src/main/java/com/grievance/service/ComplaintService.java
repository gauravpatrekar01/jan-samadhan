package com.grievance.service;

import com.grievance.model.Complaint;
import com.grievance.model.ComplaintStatusHistory;
import com.grievance.model.User;
import com.grievance.repository.ComplaintRepository;
import com.grievance.repository.ComplaintStatusHistoryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class ComplaintService {

    private final ComplaintRepository complaintRepository;
    private final ComplaintStatusHistoryRepository statusHistoryRepository;

    public Complaint createComplaint(Complaint complaint, User user) {
        complaint.setUser(user);
        return complaintRepository.save(complaint);
    }

    public List<Complaint> getMyComplaints(User user) {
        return complaintRepository.findByUser(user);
    }
    
    public List<Complaint> getAllComplaints() {
        return complaintRepository.findAll();
    }

    public Complaint getComplaintById(Long id) {
        return complaintRepository.findById(id).orElseThrow();
    }

    public Complaint updateStatus(Long id, String status, String remarks) {
        Complaint complaint = complaintRepository.findById(id).orElseThrow();
        complaint.setStatus(status);
        
        ComplaintStatusHistory history = ComplaintStatusHistory.builder()
                .complaint(complaint)
                .status(status)
                .remarks(remarks)
                .build();
        statusHistoryRepository.save(history);
        
        return complaintRepository.save(complaint);
    }
    
    public void deleteComplaint(Long id) {
        complaintRepository.deleteById(id);
    }
}
