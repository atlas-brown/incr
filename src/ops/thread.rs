use anyhow::{Result, anyhow};
use std::sync::{Arc, Condvar, Mutex};
use std::thread::{self, JoinHandle};

use crate::config::PARALLEL_SIZE;

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

pub(crate) fn parallel_process<T, F, O>(data: &[T], function: F) -> Result<Vec<O>>
where
    T: Sync,
    F: Fn(&[T]) -> Result<O> + Sync,
    O: Send,
{
    let num_chunks = data.len().div_ceil(PARALLEL_SIZE);
    if num_chunks <= 1 {
        return Ok(vec![function(data)?]);
    }

    thread::scope(|scope| {
        let mut threads = Vec::with_capacity(num_chunks);
        let mut results = Vec::with_capacity(num_chunks);
        for chunk in data.chunks(PARALLEL_SIZE) {
            threads.push(scope.spawn(|| function(chunk)));
        }
        for thread in threads {
            results.push(thread.join().map_err(|e| anyhow!("{e:?}"))??);
        }
        Ok(results)
    })
}
