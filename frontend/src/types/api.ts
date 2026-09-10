export type ApiState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string };

export type UploadStage =
  | 'idle'
  | 'dragging'
  | 'selected'
  | 'uploading'
  | 'profiling'
  | 'analyzing'
  | 'processing'
  | 'success'
  | 'error';
