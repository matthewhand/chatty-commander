import React, { useCallback, useState } from "react";
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  LinearProgress,
} from "@mui/material";
import {
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Storage as StorageIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8100";

interface ModelFile {
  name: string;
  path: string;
  size_bytes: number;
  size_human: string;
  modified: string;
  state: string | null;
}

interface ModelListResponse {
  models: ModelFile[];
  total_count: number;
  total_size_bytes: number;
  total_size_human: string;
}

const ModelsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: "success" | "error" | "info";
  }>({ open: false, message: "", severity: "info" });
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState<string | null>(null);

  // Fetch model files
  const {
    data: modelsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<ModelListResponse>({
    queryKey: ["modelFiles"],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/api/v1/models/files`);
      if (!response.ok) {
        throw new Error("Failed to fetch model files");
      }
      return response.json();
    },
  });

  // Download file
  const handleDownload = useCallback(async (filename: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/models/download/${encodeURIComponent(filename)}`
      );
      if (!response.ok) {
        throw new Error("Failed to download file");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setSnackbar({
        open: true,
        message: `Downloaded ${filename}`,
        severity: "success",
      });
    } catch (err) {
      setSnackbar({
        open: true,
        message: `Download failed: ${(err as Error).message}`,
        severity: "error",
      });
    }
  }, []);

  // Delete file mutation
  const deleteMutation = useMutation({
    mutationFn: async (filename: string) => {
      const response = await fetch(
        `${API_BASE}/api/v1/models/files/${encodeURIComponent(filename)}`,
        { method: "DELETE" }
      );
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to delete file");
      }
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["modelFiles"] });
      setSnackbar({
        open: true,
        message: data.message,
        severity: "success",
      });
      setDeleteDialogOpen(false);
      setFileToDelete(null);
    },
    onError: (err: Error) => {
      setSnackbar({
        open: true,
        message: `Delete failed: ${err.message}`,
        severity: "error",
      });
    },
  });

  // Upload file
  const handleUpload = useCallback(async () => {
    if (!uploadFile) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      if (uploadState) {
        formData.append("state", uploadState);
      }

      const response = await fetch(`${API_BASE}/api/v1/models/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to upload file");
      }

      const data = await response.json();
      queryClient.invalidateQueries({ queryKey: ["modelFiles"] });
      setSnackbar({
        open: true,
        message: data.message,
        severity: "success",
      });
      setUploadDialogOpen(false);
      setUploadFile(null);
      setUploadState("");
    } catch (err) {
      setSnackbar({
        open: true,
        message: `Upload failed: ${(err as Error).message}`,
        severity: "error",
      });
    } finally {
      setUploading(false);
    }
  }, [uploadFile, uploadState, queryClient]);

  const getStateColor = (state: string | null) => {
    switch (state) {
      case "idle":
        return "default";
      case "computer":
        return "primary";
      case "chatty":
        return "secondary";
      default:
        return "info";
    }
  };

  return (
    <Box
      sx={{
        flexGrow: 1,
        p: 3,
        background: "linear-gradient(to right bottom, #2e3a4d, #1a202c)",
        minHeight: "calc(100vh - 64px)",
      }}
    >
      <Container maxWidth="lg">
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 4 }}
        >
          <Typography variant="h4" sx={{ color: "white" }}>
            <StorageIcon sx={{ mr: 1, verticalAlign: "middle" }} />
            Voice Models
          </Typography>
          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => refetch()}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<UploadIcon />}
              onClick={() => setUploadDialogOpen(true)}
            >
              Upload Model
            </Button>
          </Stack>
        </Stack>

        {isLoading && <LinearProgress />}

        {isError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            Failed to load models: {(error as Error)?.message}
          </Alert>
        )}

        {modelsData && (
          <>
            {/* Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} sm={4}>
                <Card sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Total Models
                    </Typography>
                    <Typography variant="h4">{modelsData.total_count}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Card sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      Total Size
                    </Typography>
                    <Typography variant="h4">
                      {modelsData.total_size_human}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Card sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Typography color="text.secondary" gutterBottom>
                      States
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      {["idle", "computer", "chatty"].map((s) => (
                        <Chip
                          key={s}
                          label={s}
                          size="small"
                          color={getStateColor(s) as "default" | "primary" | "secondary" | "info"}
                        />
                      ))}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Models Table */}
            <Card sx={{ borderRadius: 2 }}>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Filename</TableCell>
                      <TableCell>State</TableCell>
                      <TableCell>Size</TableCell>
                      <TableCell>Modified</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {modelsData.models.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} align="center">
                          <Typography color="text.secondary" sx={{ py: 4 }}>
                            No ONNX model files found. Upload a model to get started.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      modelsData.models.map((model) => (
                        <TableRow key={model.path}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {model.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {model.path}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {model.state ? (
                              <Chip
                                label={model.state}
                                size="small"
                                color={
                                  getStateColor(model.state) as
                                    | "default"
                                    | "primary"
                                    | "secondary"
                                    | "info"
                                }
                              />
                            ) : (
                              <Chip label="general" size="small" variant="outlined" />
                            )}
                          </TableCell>
                          <TableCell>{model.size_human}</TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {new Date(model.modified).toLocaleDateString()}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(model.modified).toLocaleTimeString()}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <IconButton
                              size="small"
                              onClick={() => handleDownload(model.name)}
                              title="Download"
                            >
                              <DownloadIcon />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => {
                                setFileToDelete(model.name);
                                setDeleteDialogOpen(true);
                              }}
                              title="Delete"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Card>
          </>
        )}
      </Container>

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => !uploading && setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Upload ONNX Model</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Button
              variant="outlined"
              component="label"
              startIcon={<UploadIcon />}
              disabled={uploading}
            >
              {uploadFile ? uploadFile.name : "Select ONNX File"}
              <input
                type="file"
                hidden
                accept=".onnx"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              />
            </Button>
            <FormControl fullWidth>
              <InputLabel>Target State (Optional)</InputLabel>
              <Select
                value={uploadState}
                label="Target State (Optional)"
                onChange={(e) => setUploadState(e.target.value)}
                disabled={uploading}
              >
                <MenuItem value="">General (wakewords)</MenuItem>
                <MenuItem value="idle">Idle State</MenuItem>
                <MenuItem value="computer">Computer State</MenuItem>
                <MenuItem value="chatty">Chatty State</MenuItem>
              </Select>
            </FormControl>
            <Alert severity="info">
              ONNX models are used for wake word detection. Upload trained models
              to add new voice commands.
            </Alert>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setUploadDialogOpen(false);
              setUploadFile(null);
              setUploadState("");
            }}
            disabled={uploading}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleUpload}
            disabled={!uploadFile || uploading}
          >
            {uploading ? "Uploading..." : "Upload"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{fileToDelete}"? This action cannot
            be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            onClick={() => fileToDelete && deleteMutation.mutate(fileToDelete)}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: "100%" }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ModelsPage;
