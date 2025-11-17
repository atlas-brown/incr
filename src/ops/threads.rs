use anyhow::{Result, anyhow};
use std::sync::{Arc, Condvar, Mutex};
use std::thread::JoinHandle;

#[derive(Clone, Debug)]
pub(crate) struct SignalSender {
    active: Arc<Mutex<bool>>,
    condition: Arc<Condvar>,
}

impl SignalSender {
    pub(crate) fn set_active(&self) {
        *self.active.lock().unwrap() = true;
        self.condition.notify_all();
    }
}

#[derive(Clone, Debug)]
pub(crate) struct SignalReceiver {
    active: Arc<Mutex<bool>>,
    condition: Arc<Condvar>,
}

impl SignalReceiver {
    pub(crate) fn check_active(&self) -> bool {
        *self.active.lock().unwrap()
    }

    pub(crate) fn wait_until_active(&self) {
        let mut active = self.active.lock().unwrap();
        while !*active {
            active = self.condition.wait(active).unwrap();
        }
    }
}

pub(crate) fn create_signal() -> (SignalSender, SignalReceiver) {
    let active = Arc::new(Mutex::new(false));
    let condition = Arc::new(Condvar::new());
    (
        SignalSender {
            active: Arc::clone(&active),
            condition: Arc::clone(&condition),
        },
        SignalReceiver { active, condition },
    )
}

pub(crate) fn join<T>(thread: JoinHandle<T>) -> Result<T> {
    thread.join().map_err(|e| anyhow!("{e:?}"))
}
