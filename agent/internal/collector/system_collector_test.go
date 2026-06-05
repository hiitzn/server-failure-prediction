package collector

import (
    "context"
    "testing"
)

func TestSystemCollector_Collect(t *testing.T) {
    c := NewSystemCollector("/") // для Windows можно "C:"
    
    metrics, err := c.Collect(context.Background())
    if err != nil {
        t.Fatalf("Collect failed: %v", err)
    }
    
    // Проверяем диапазоны значений
    if metrics.CPUPercent < 0 || metrics.CPUPercent > 100 {
        t.Errorf("CPUPercent out of range: %f", metrics.CPUPercent)
    }
    if metrics.MemoryPercent < 0 || metrics.MemoryPercent > 100 {
        t.Errorf("MemoryPercent out of range: %f", metrics.MemoryPercent)
    }
    if metrics.DiskPercent < 0 || metrics.DiskPercent > 100 {
        t.Errorf("DiskPercent out of range: %f", metrics.DiskPercent)
    }
}

func TestSystemCollector_ReadCPU(t *testing.T) {
    c := NewSystemCollector("/")
    
    cpu, err := c.readCPU(context.Background())
    if err != nil {
        t.Fatalf("readCPU failed: %v", err)
    }
    if cpu < 0 || cpu > 100 {
        t.Errorf("CPU out of range: %f", cpu)
    }
}

func TestSystemCollector_ReadMemory(t *testing.T) {
    c := NewSystemCollector("/")
    
    mem, err := c.readMemory()
    if err != nil {
        t.Fatalf("readMemory failed: %v", err)
    }
    if mem < 0 || mem > 100 {
        t.Errorf("Memory out of range: %f", mem)
    }
}

func TestSystemCollector_ReadDisk(t *testing.T) {
    c := NewSystemCollector("/")
    
    disk, err := c.readDisk()
    if err != nil {
        t.Fatalf("readDisk failed: %v", err)
    }
    if disk < 0 || disk > 100 {
        t.Errorf("Disk out of range: %f", disk)
    }
}