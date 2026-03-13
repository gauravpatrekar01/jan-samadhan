package com.grievance.controller;

import com.grievance.model.Complaint;
import com.grievance.model.User;
import com.grievance.service.ComplaintService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/complaints")
@RequiredArgsConstructor
public class ComplaintController {

    private final ComplaintService service;

    @PostMapping
    public ResponseEntity<Complaint> createComplaint(
            @RequestBody Complaint complaint,
            @AuthenticationPrincipal User user
    ) {
        return ResponseEntity.ok(service.createComplaint(complaint, user));
    }

    @GetMapping
    public ResponseEntity<List<Complaint>> getComplaints(
            @AuthenticationPrincipal User user
    ) {
        if (user.getRole().name().equals("CITIZEN")) {
            return ResponseEntity.ok(service.getMyComplaints(user));
        }
        return ResponseEntity.ok(service.getAllComplaints());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Complaint> getComplaint(@PathVariable Long id) {
        return ResponseEntity.ok(service.getComplaintById(id));
    }

    @PutMapping("/{id}/status")
    public ResponseEntity<Complaint> updateStatus(
            @PathVariable Long id,
            @RequestBody Map<String, String> updateRequest
    ) {
        return ResponseEntity.ok(service.updateStatus(id, updateRequest.get("status"), updateRequest.get("remarks")));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteComplaint(@PathVariable Long id) {
        service.deleteComplaint(id);
        return ResponseEntity.noContent().build();
    }
}
