const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(method, path, body, isForm = false) {
    const opts = { method, headers: {} };
    if (body) {
        if (isForm) {
            opts.body = body;
        } else {
            opts.headers["Content-Type"] = "application/json";
            opts.body = JSON.stringify(body);
        }
    }
    const res = await fetch(`${BASE_URL}${path}`, opts);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Request failed");
    }
    return res.json();
}

export const api = {
    /** GET /file_list */
    getFileList: () => request("GET", "/file_list"),

    /** POST /upload_file */
    uploadFile: (file) => {
        const fd = new FormData();
        fd.append("file", file);
        return request("POST", "/upload_file", fd, true);
    },

    /** GET /summary/{file_name} */
    getSummary: (fileName) =>
        request("GET", `/summary/${encodeURIComponent(fileName)}`),

    /** GET /plan/{file_name}/{query} */
    getPlan: (fileName, query) =>
        request(
            "GET",
            `/plan/${encodeURIComponent(fileName)}/${encodeURIComponent(query)}`
        ),

    /** POST /negotiate */
    negotiate: (clauses, risks) =>
        request("POST", "/negotiate", { clauses, risks }),

    /** GET / (health check) */
    health: () => request("GET", "/"),
};
