-- =========================================================================
-- Tabla de log de errores (complemento al script principal)
-- =========================================================================

USE PruebaNomina;
GO

CREATE TABLE Novedades_HorasExtras_Errores (
    IdError            INT IDENTITY(1,1) PRIMARY KEY,
    DocumentoEmpleado  VARCHAR(20),
    TipoHoraExtra      VARCHAR(50),
    CantidadHoras      VARCHAR(20),   -- se guarda el valor crudo
    FechaReporte       VARCHAR(20),   -- se guarda el valor crudo
    MotivoError        VARCHAR(500)   NOT NULL,
    FechaProcesamiento DATETIME       DEFAULT GETDATE()
);
GO
