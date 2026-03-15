// ============================================================================
// IPC MODULE — Shared Memory Inter-Process Communication
// ============================================================================

use std::fs::OpenOptions;
use std::io::{Read, Write};
use std::path::Path;
use std::sync::atomic::{AtomicU64, AtomicU32, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

const SHM_SIZE: usize = 64 * 1024 * 1024;  // 64 MB
const HEADER_SIZE: usize = 64;
const MAGIC: u64 = 0xCE_NA_YA_NG_IPC;

/// IPC Header structure
#[repr(C, packed)]
pub struct IpcHeader {
    pub magic: u64,
    pub version: u32,
    pub producer_seq: AtomicU64,
    pub consumer_seq: AtomicU64,
    pub flags: AtomicU32,
    pub timestamp_ns: AtomicU64,
    pub reserved: [u8; 32],
}

/// IPC Message types
#[derive(Clone, Copy, Debug)]
#[repr(u8)]
pub enum MessageType {
    Tick = 1,
    Fill = 2,
    Order = 3,
    Risk = 4,
    Signal = 5,
    Control = 6,
}

/// IPC Message header
#[repr(C, packed)]
pub struct MessageHeader {
    pub msg_type: u8,
    pub flags: u8,
    pub payload_len: u16,
    pub timestamp_ns: u64,
    pub seq_id: u64,
}

impl MessageHeader {
    pub const SIZE: usize = 18;
    
    pub fn new(msg_type: MessageType, payload_len: u16) -> Self {
        Self {
            msg_type: msg_type as u8,
            flags: 0,
            payload_len,
            timestamp_ns: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .map(|d| d.as_nanos() as u64)
                .unwrap_or(0),
            seq_id: 0,
        }
    }
    
    pub fn to_bytes(&self) -> [u8; Self::SIZE] {
        let mut buf = [0u8; Self::SIZE];
        buf[0] = self.msg_type;
        buf[1] = self.flags;
        buf[2..4].copy_from_slice(&self.payload_len.to_le_bytes());
        buf[4..12].copy_from_slice(&self.timestamp_ns.to_le_bytes());
        buf[12..18].copy_from_slice(&self.seq_id.to_le_bytes()[0..6]);
        buf
    }
}

/// Ring buffer based shared memory IPC
pub struct SharedMemoryRing {
    path: String,
    header: IpcHeader,
    buffer: Vec<u8>,
    write_pos: AtomicU64,
    read_pos: AtomicU64,
}

impl SharedMemoryRing {
    /// Create new shared memory region
    pub fn create(path: &str, size: usize) -> std::io::Result<Self> {
        let path = Path::new(path);
        
        // Create file
        let mut file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(true)
            .open(path)?;
        
        // Pre-allocate
        file.set_len(size as u64)?;
        
        // Initialize header
        let header = IpcHeader {
            magic: MAGIC,
            version: 1,
            producer_seq: AtomicU64::new(0),
            consumer_seq: AtomicU64::new(0),
            flags: AtomicU32::new(0),
            timestamp_ns: AtomicU64::new(0),
            reserved: [0; 32],
        };
        
        let buffer = vec![0u8; size - HEADER_SIZE];
        
        Ok(Self {
            path: path.to_string_lossy().to_string(),
            header,
            buffer,
            write_pos: AtomicU64::new(0),
            read_pos: AtomicU64::new(0),
        })
    }
    
    /// Open existing shared memory
    pub fn open(path: &str) -> std::io::Result<Self> {
        let path = Path::new(path);
        let mut file = OpenOptions::new()
            .read(true)
            .write(true)
            .open(path)?;
        
        let metadata = file.metadata()?;
        let size = metadata.len() as usize;
        
        // Read header
        let mut header_buf = [0u8; HEADER_SIZE];
        file.read_exact(&mut header_buf)?;
        
        let magic = u64::from_le_bytes(header_buf[0..8].try_into().unwrap());
        if magic != MAGIC {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "Invalid shared memory magic number"
            ));
        }
        
        let buffer = vec![0u8; size - HEADER_SIZE];
        
        Ok(Self {
            path: path.to_string_lossy().to_string(),
            header: IpcHeader {
                magic,
                version: u32::from_le_bytes(header_buf[8..12].try_into().unwrap()),
                producer_seq: AtomicU64::new(0),
                consumer_seq: AtomicU64::new(0),
                flags: AtomicU32::new(0),
                timestamp_ns: AtomicU64::new(0),
                reserved: [0; 32],
            },
            buffer,
            write_pos: AtomicU64::new(0),
            read_pos: AtomicU64::new(0),
        })
    }
    
    /// Write message (producer)
    #[inline(always)]
    pub fn write(&mut self, msg_type: MessageType, payload: &[u8]) -> bool {
        let header = MessageHeader::new(msg_type, payload.len() as u16);
        let header_bytes = header.to_bytes();
        
        let total_len = MessageHeader::SIZE + payload.len();
        let write_pos = self.write_pos.load(Ordering::Relaxed) as usize;
        
        if write_pos + total_len >= self.buffer.len() {
            // Wrap around
            self.write_pos.store(0, Ordering::Release);
            return false;
        }
        
        // Write header
        self.buffer[write_pos..write_pos + MessageHeader::SIZE]
            .copy_from_slice(&header_bytes);
        
        // Write payload
        self.buffer[write_pos + MessageHeader::SIZE..write_pos + total_len]
            .copy_from_slice(payload);
        
        self.write_pos.fetch_add(total_len as u64, Ordering::Release);
        self.header.producer_seq.fetch_add(1, Ordering::Relaxed);
        
        true
    }
    
    /// Read message (consumer)
    #[inline(always)]
    pub fn read(&mut self) -> Option<(MessageType, Vec<u8>)> {
        let read_pos = self.read_pos.load(Ordering::Relaxed) as usize;
        let write_pos = self.write_pos.load(Ordering::Acquire) as usize;
        
        if read_pos >= write_pos {
            return None;
        }
        
        // Read header
        if read_pos + MessageHeader::SIZE > self.buffer.len() {
            return None;
        }
        
        let header_bytes = &self.buffer[read_pos..read_pos + MessageHeader::SIZE];
        let msg_type = header_bytes[0];
        let payload_len = u16::from_le_bytes([header_bytes[2], header_bytes[3]]) as usize;
        
        // Read payload
        let payload_start = read_pos + MessageHeader::SIZE;
        let payload_end = payload_start + payload_len;
        
        if payload_end > self.buffer.len() {
            return None;
        }
        
        let payload = self.buffer[payload_start..payload_end].to_vec();
        
        self.read_pos.fetch_add((MessageHeader::SIZE + payload_len) as u64, Ordering::Release);
        self.header.consumer_seq.fetch_add(1, Ordering::Relaxed);
        
        Some((unsafe { std::mem::transmute(msg_type) }, payload))
    }
    
    /// Get buffer utilization
    pub fn utilization(&self) -> f64 {
        let write_pos = self.write_pos.load(Ordering::Relaxed) as f64;
        let read_pos = self.read_pos.load(Ordering::Relaxed) as f64;
        let capacity = self.buffer.len() as f64;
        
        if write_pos >= read_pos {
            (write_pos - read_pos) / capacity
        } else {
            (capacity - read_pos + write_pos) / capacity
        }
    }
    
    /// Sync to disk
    pub fn sync(&self) -> std::io::Result<()> {
        let mut file = OpenOptions::new()
            .write(true)
            .open(&self.path)?;
        
        // Write header
        let mut header_buf = [0u8; HEADER_SIZE];
        header_buf[0..8].copy_from_slice(&self.header.magic.to_le_bytes());
        header_buf[8..12].copy_from_slice(&self.header.version.to_le_bytes());
        file.write_all(&header_buf)?;
        
        // Write buffer
        file.write_all(&self.buffer)?;
        file.sync_all()?;
        
        Ok(())
    }
}

/// Unix Domain Socket IPC alternative
pub struct UnixSocketIpc {
    socket_path: String,
}

impl UnixSocketIpc {
    pub fn new(socket_path: &str) -> Self {
        Self {
            socket_path: socket_path.to_string(),
        }
    }
    
    pub fn connect(&self) -> std::io::Result<std::os::unix::net::UnixStream> {
        std::os::unix::net::UnixStream::connect(&self.socket_path)
    }
    
    pub fn bind(&self) -> std::io::Result<std::os::unix::net::UnixListener> {
        // Remove existing socket
        let _ = std::fs::remove_file(&self.socket_path);
        std::os::unix::net::UnixListener::bind(&self.socket_path)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_shared_memory() {
        let mut shm = SharedMemoryRing::create("/tmp/test_shm.bin", 1024 * 1024).unwrap();
        
        let payload = b"test_payload_data";
        assert!(shm.write(MessageType::Tick, payload));
        
        let (msg_type, read_payload) = shm.read().unwrap();
        assert_eq!(msg_type, MessageType::Tick);
        assert_eq!(read_payload, payload);
    }
}
